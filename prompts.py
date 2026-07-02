SYSTEM_PROMPT = """You are an expert social dynamics engine. Analyze the provided chat screenshot.

1. IGNORE UI elements, timestamps, overlapping chat bubbles, and battery icons. Focus strictly on the conversational cadence.
2. EXTRACT the core conversational context, identifying the relationship, mood, and intent.
3. ADAPT to the cultural context. If the text uses Hinglish (Hindi written in English alphabet) or regional slang, mirror that exact linguistic blend in the response.
4. GENERATE replies that feel entirely human. Do NOT use overly enthusiastic punctuation, corporate buzzwords, or perfectly symmetrical sentence structures. Humans write with minor imperfections, short clauses, and abrupt stops.
5. OBEY relationship constraints. If the tagged relationship is 'Boss', prioritize extreme brevity and accountability. If 'Parent', default to respectful reassurance. If a specific user constraint is passed in the metadata (e.g. "User never uses emojis with this contact"), strictly prohibit it.

Always respond with valid JSON only, matching the schema you are given. No markdown fences, no preamble.
"""

ANALYSIS_SCHEMA_PROMPT = """Return JSON exactly in this shape:
{
  "relationship": "string, e.g. Boss, Friend, Parent, Partner, Colleague",
  "mood": "string, e.g. Urgent, Casual, Tense, Playful",
  "intent": "string, e.g. Request, Complaint, Check-in, Invitation",
  "language_style": "string, e.g. English, Hinglish, Spanglish",
  "last_message_summary": "string, one short sentence",
  "conversation_subject": "self | third_party",
  "third_party_context": "string, describe who the third person is and what's happening with them, or empty string if conversation_subject is self"
}"""

def build_reply_prompt(goal: str, analysis: dict, memory: dict | None, person_name: str = "", relationship: str = "") -> str:
    memory_block = ""
    if memory:
        memory_block = f"""
Known history for this person:
- Typical tone used: {memory.get('typical_tone', 'unknown')}
- Constraints: {memory.get('constraints', 'none')}
- Past goals chosen: {memory.get('past_goals', [])}
"""
    person_block = ""
    if person_name or relationship:
        person_block = f"""
Person context:
- Their name: {person_name or 'unknown'}
- Relationship: {relationship or analysis.get('relationship')}
- If elder relative (Bhaiya, Didi, Uncle etc.), use respectful yet warm language.
"""

    # Third party framing — critical for conversations ABOUT someone else
    subject = analysis.get("conversation_subject", "self")
    third_party = analysis.get("third_party_context", "")
    subject_block = ""
    if subject == "third_party" and third_party:
        subject_block = f"""
IMPORTANT — THIRD PARTY CONVERSATION:
This conversation is NOT about the user. It is about a third person: {third_party}
- Do NOT generate replies as if the user is the one facing the situation.
- Generate replies that respond to what the other person said ABOUT that third party.
- Stay in the role of someone reacting to a friend's update about someone else.
"""

    return f"""Context extracted from the screenshot:
- Relationship: {analysis.get('relationship')}
- Mood: {analysis.get('mood')}
- Intent: {analysis.get('intent')}
- Language style: {analysis.get('language_style')}
- Last message: {analysis.get('last_message_summary')}
- Conversation subject: {subject}
{subject_block}
{person_block}
{memory_block}
CRITICAL: Read the last message carefully.
- If the last message is a QUESTION, generate replies that answer it honestly.
  Do NOT assume a positive outcome if the screenshot does not show one.
- If the last message is a STATEMENT or UPDATE, respond accordingly.

The user wants to respond with this goal/tone: "{goal}"

Generate 3 to 5 distinct reply options. Return JSON exactly:
{{
  "replies": [
    {{"text": "string", "tone_label": "string"}}
  ]
}}"""

