-- ==============================================================================
-- OMNI-FUSION CHAT MESSAGES MIGRATION
-- ==============================================================================

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sender_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Service Role full access
CREATE POLICY "Service Role Full Access chat_messages" ON chat_messages FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Users can read messages where they are the sender or receiver
CREATE POLICY "Users can view their chat messages" ON chat_messages FOR SELECT USING (
    auth.uid() = sender_id OR auth.uid() = receiver_id
);

-- Users can insert messages where they are the sender
CREATE POLICY "Users can send chat messages" ON chat_messages FOR INSERT WITH CHECK (
    auth.uid() = sender_id
);

-- Users can update (e.g. mark as read) messages where they are the receiver
CREATE POLICY "Users can update received chat messages" ON chat_messages FOR UPDATE USING (
    auth.uid() = receiver_id
);
