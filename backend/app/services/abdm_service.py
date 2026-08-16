from datetime import datetime
from typing import Dict, Any, List

class AbdmService:
    @staticmethod
    def generate_fhir_diagnostic_report(patient: dict, predictions: List[dict]) -> dict:
        """
        Maps the platform's profile and prediction data into a FHIR R4 DiagnosticReport
        JSON shape, suitable for ABDM health record exchange.
        """
        # Basic FHIR Patient resource included as a contained resource or referenced
        patient_ref = f"Patient/{patient.get('id', 'unknown')}"
        
        # We will wrap the predictions as Observations within a DiagnosticReport
        observations = []
        for pred in predictions:
            obs = {
                "resourceType": "Observation",
                "id": f"obs-{pred.get('id')}",
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "71342-0",
                            "display": "Patient risk score"
                        }
                    ]
                },
                "subject": {
                    "reference": patient_ref
                },
                "valueQuantity": {
                    "value": round(pred.get("risk_score", 0.0), 4),
                    "unit": "%",
                    "system": "http://unitsofmeasure.org"
                },
                "issued": pred.get("created_at")
            }
            observations.append(obs)
            
        report = {
            "resourceType": "DiagnosticReport",
            "id": f"dr-{patient.get('id', 'unknown')}-{int(datetime.now().timestamp())}",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                            "code": "LAB",
                            "display": "Laboratory"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "11502-2",
                        "display": "Laboratory report"
                    }
                ]
            },
            "subject": {
                "reference": patient_ref
            },
            "issued": datetime.now().isoformat(),
            "result": [{"reference": f"#{obs['id']}"} for obs in observations],
            "contained": observations
        }
        
        return report

    @staticmethod
    def notify_gateway(callback_url: str, payload: dict) -> bool:
        """
        Send a webhook notification to the ABDM gateway.
        Includes strict SSRF mitigation to prevent dialing local IPs or non-gov domains.
        """
        from urllib.parse import urlparse
        import ipaddress
        import socket
        
        parsed = urlparse(callback_url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid callback URL")
            
        # Allow-list check
        if not hostname.endswith(".gov.in") and not hostname.endswith(".ndhm.gov.in"):
            # For sandbox testing, we might want to allow localhost but that's what SSRF prevents.
            # In a real environment, we enforce the gov.in domain.
            raise ValueError("Callback URL must belong to a valid ABDM .gov.in domain")
            
        # Block-list IP resolution check
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                raise ValueError("Resolved IP is in a blocked private/local range (SSRF prevented)")
        except socket.gaierror:
            raise ValueError("Could not resolve callback hostname")
            
        # In a real implementation, we would use requests.post here
        # import requests
        # requests.post(callback_url, json=payload, timeout=5)
        return True

abdm_service = AbdmService()
