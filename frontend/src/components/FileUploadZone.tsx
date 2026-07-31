'use client';

import { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

import { UploadHistoricalResponse } from '@/lib/types';

interface FileUploadZoneProps {
  mode?: 'blood' | 'ecg';
  onSessionCreated: (response: UploadHistoricalResponse, previewUrl?: string) => void;
}

export default function FileUploadZone({ mode = 'blood', onSessionCreated }: FileUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setStatus('uploading');
    setErrorMessage('');
    
    let previewUrl: string | undefined;
    if (selectedFile.type.startsWith('image/') || selectedFile.type === 'application/pdf') {
      previewUrl = URL.createObjectURL(selectedFile);
    }
    
    try {
      let res;
      if (mode === 'ecg') {
        res = await api.uploadEcgReport(selectedFile);
      } else {
        if (selectedFile.name.toLowerCase().endsWith('.csv')) {
          res = await api.uploadHistoricalCSV(selectedFile);
        } else {
          res = await api.uploadBloodReport(selectedFile);
        }
      }
      setStatus('success');
      onSessionCreated(res, previewUrl);
    } catch (err: unknown) {
      setStatus('error');
      setErrorMessage(err instanceof Error ? err.message : 'Failed to upload file');
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          isDragging ? 'border-slate-400 bg-slate-800' : 'border-slate-700 bg-slate-900 hover:border-slate-500'
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          accept=".csv,.pdf,.jpg,.jpeg,.png"
          className="hidden"
          ref={fileInputRef}
          onChange={(e) => {
            if (e.target.files && e.target.files.length > 0) {
              handleFileSelect(e.target.files[0]);
            }
          }}
        />
        
        {status === 'idle' && (
          <div className="flex flex-col items-center cursor-pointer">
            <UploadCloud className="w-12 h-12 text-slate-400 mb-4" />
            <p className="text-slate-300 font-medium">Click or drag {mode === 'ecg' ? 'ECG' : 'Blood'} Report here</p>
            <p className="text-sm text-slate-500 mt-1">{mode === 'ecg' ? 'PDF, JPG, or PNG' : 'PDF, JPG, PNG, or CSV'}</p>
          </div>
        )}

        {status === 'uploading' && (
          <div className="flex flex-col items-center">
            <Loader2 className="w-12 h-12 text-slate-400 mb-4 animate-spin" />
            <p className="text-slate-300 font-medium">Uploading & Imputing...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="flex flex-col items-center">
            <CheckCircle className="w-12 h-12 text-green-500 mb-4" />
            <p className="text-green-400 font-medium">Upload Complete</p>
            <p className="text-sm text-slate-400 mt-1">{file?.name}</p>
          </div>
        )}

        {status === 'error' && (
          <div className="flex flex-col items-center">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-red-400 font-medium">Upload Failed</p>
            <p className="text-sm text-slate-400 mt-1">{errorMessage}</p>
          </div>
        )}
      </div>
    </div>
  );
}
