import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from groq import Groq
from groq import APIError as GroqAPIError, RateLimitError, AuthenticationError as GroqAuthError
import google.generativeai as genai
from google.api_core import exceptions as gemini_exceptions
from app.core.config import settings

logger = logging.getLogger(__name__)

LANG_MAP = {
    "en": "English", "hi": "Hindi", "te": "Telugu", "ta": "Tamil", "bn": "Bengali", "mr": "Marathi"
}

TRIAGE_COLORS = {"RED", "YELLOW", "GREEN"}
DEFAULT_DURATIONS = {"RED": 15, "YELLOW": 10, "GREEN": 5}
AVG_WALKING_TIME_MINUTES = 15
ARRIVAL_BUFFER_MINUTES = 5
SMS_MAX_CHARS = 300
SMS_SAFE_CHARS = 160
MIN_CLUSTER_SIZE = 3
CONFIDENCE_THRESHOLD = 0.6

_groq_client: Optional[Groq] = None
_gemini_model = None
_clients_initialized = False

def init_ai_clients():
    global _groq_client, _gemini_model, _clients_initialized
    if _clients_initialized:
        return _groq_client is not None or _gemini_model is not None
    _clients_initialized = True
    groq_key = getattr(settings, 'GROQ_API_KEY', None)
    gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
    if groq_key and groq_key not in ["your_groq_key_here", ""]:
        try:
            _groq_client = Groq(api_key=groq_key.strip())
            _groq_client.models.list()
            logger.info("Groq client initialized")
        except Exception as e:
            logger.error(f"Groq init failed: {e}")
    if gemini_key and gemini_key not in ["your_gemini_key_here", ""]:
        try:
            genai.configure(api_key=gemini_key.strip())
            _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            logger.info("Gemini client initialized")
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")
    return _groq_client is not None or _gemini_model is not None

init_ai_clients()

def _extract_json(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```", 2)
            if len(parts) >= 3:
                cleaned = parts[1].strip()
                if '\n' in cleaned:
                    cleaned = cleaned.split('\n', 1)[1]
                cleaned = cleaned.rstrip('`').strip()
                return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    try:
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    try:
        fixed = text.replace("'", '"').replace(',}', '}').replace(',]', ']')
        match = re.search(r'\{.*\}', fixed, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, AttributeError):
        pass
    logger.warning(f"Failed to extract JSON from: {text[:200]}...")
    return {}

def _call_llm_with_fallback(prompt: str, temperature: float = 0.2, max_tokens: int = 500, max_retries: int = 3, model: str = "llama-3.1-8b-instant") -> Optional[str]:
    last_error = None
    for provider_name, client, is_gemini in [("Groq", _groq_client, False), ("Gemini", _gemini_model, True)]:
        if client is None:
            continue
        for attempt in range(max_retries):
            try:
                if is_gemini:
                    response = client.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        )
                    )
                    if response and response.text:
                        return response.text.strip()
                else:
                    completion = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=0.95,
                        timeout=30
                    )
                    if completion and completion.choices and completion.choices[0].message.content:
                        return completion.choices[0].message.content.strip()
                logger.warning(f"{provider_name} attempt {attempt + 1}: Empty response")
            except (RateLimitError, gemini_exceptions.ResourceExhausted) as e:
                last_error = e
                delay = getattr(e, 'retry_after', None)
                if delay:
                    time.sleep(float(delay) + 1)
                else:
                    time.sleep((2 ** attempt) + attempt)
                continue
            except (GroqAuthError, gemini_exceptions.PermissionDenied) as e:
                logger.error(f"{provider_name} auth failed: {e}")
                break
            except (GroqAPIError, gemini_exceptions.GoogleAPIError) as e:
                last_error = e
                logger.error(f"{provider_name} API error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 0.5)
                continue
            except Exception as e:
                last_error = e
                logger.error(f"{provider_name} unexpected error: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 0.5)
                continue
        if last_error:
            logger.warning(f"{provider_name} exhausted, trying fallback")
    if last_error:
        logger.error(f"All providers exhausted. Last error: {last_error}")
    return None

def _validate_multilingual_text(text: str, language: str) -> bool:
    if language == "en":
        return text.isascii() or len(text) > 0
    script_patterns = {
        "hi": r'[\u0900-\u097F]',
        "te": r'[\u0C00-\u0C7F]',
        "ta": r'[\u0B80-\u0BFF]',
        "bn": r'[\u0980-\u09FF]',
        "mr": r'[\u0900-\u097F]',
    }
    pattern = script_patterns.get(language)
    if pattern:
        return bool(re.search(pattern, text))
    return True

def triage_symptom(symptom_text: str, doctor_name: str = "Doctor", language: str = "en") -> Dict[str, Any]:
    default = {"color": "GREEN", "reason": "Routine evaluation recommended", "complexity": 1}
    if not symptom_text or not symptom_text.strip():
        return default
    symptom_lower = symptom_text.lower()
    emergency_keywords = [
        "chest pain", "breathing", "unconscious", "severe bleed", "heart attack",
        "stroke", "seizure", "difficulty breathing", "बेहोश", "सीने में दर्द", "सांस"
    ]
    if any(kw in symptom_lower for kw in emergency_keywords):
        return {"color": "RED", "reason": "Immediate clinical attention required", "complexity": 3}
    lang_name = LANG_MAP.get(language, "English")
    prompt = f"""You are a senior medical officer at an Indian government hospital OPD. Provide compassionate, clinically accurate triage guidance.

Patient presentation: "{symptom_text}"
Attending physician: {doctor_name}
Respond in {lang_name}.

Return ONLY valid JSON with these exact keys:
{{
  "color": "RED" for life-threatening/emergency requiring immediate intervention, "YELLOW" for urgent conditions needing same-day evaluation, or "GREEN" for routine/non-urgent cases,
  "reason": "Concise clinical rationale in {lang_name}, maximum 5 words, no punctuation",
  "complexity": 1 for straightforward consultation, 2 for cases requiring basic diagnostics, 3 for complex presentations needing specialist input or advanced workup
}}

Clinical guidelines:
- Prioritize patient safety: when clinical uncertainty exists, assign higher acuity
- Use precise medical terminology while remaining accessible to patients
- Output ONLY the JSON object—no markdown, no explanatory text

Example: {{"color": "YELLOW", "reason": "Suspected infectious process warrants evaluation", "complexity": 2}}"""
    
    response = _call_llm_with_fallback(prompt, temperature=0.1, max_tokens=250)
    if response:
        data = _extract_json(response)
        if (data.get("color") in TRIAGE_COLORS and
            "reason" in data and
            isinstance(data.get("complexity"), int) and
            1 <= data["complexity"] <= 3):
            if language != "en" and not _validate_multilingual_text(data["reason"], language):
                logger.warning(f"Triage reason failed language validation for {language}")
                data["reason"] = default["reason"]
            return data
    logger.warning(f"Triage AI failed for symptom: {symptom_text[:50]}... Using clinical fallback")
    return default

def predict_consultation_duration(symptom_text: str, triage_color: str = "GREEN") -> int:
    base_duration = DEFAULT_DURATIONS.get(triage_color, 5)
    if not symptom_text or (_groq_client is None and _gemini_model is None):
        return base_duration
    prompt = f"""You are an experienced OPD scheduling physician. Based on clinical workflow standards:

Presenting complaint: '{symptom_text}'
Triage acuity: {triage_color}

Estimate the STANDARD consultation duration in MINUTES, accounting for:
- Focused history taking
- Targeted physical examination
- Patient education and basic management planning

Exclude waiting time, diagnostic test turnaround, or specialist referral delays.

Respond with ONLY a single integer between 2 and 30.
No units, no text, no explanation.
Example: 8"""
    
    response = _call_llm_with_fallback(prompt, temperature=0, max_tokens=20)
    if response:
        try:
            numbers = re.findall(r'\d+', response)
            if numbers:
                minutes = int(numbers[0])
                return max(2, min(minutes, 30))
        except (ValueError, IndexError) as e:
            logger.warning(f"Duration parse error: {e}")
    return base_duration

def calculate_arrival_time(
    queue_position: int,
    avg_consultation_seconds: int,
    buffer_seconds: int = 180,
    patient_travel_minutes: int = AVG_WALKING_TIME_MINUTES,
    current_time: Optional[datetime] = None
) -> Dict[str, Any]:
    now = current_time or datetime.now(timezone.utc)
    time_per_patient = avg_consultation_seconds + buffer_seconds
    estimated_wait_seconds = queue_position * time_per_patient
    import random
    variance = random.uniform(0.9, 1.1)
    estimated_wait_seconds = int(estimated_wait_seconds * variance)
    estimated_wait_minutes = estimated_wait_seconds // 60
    consultation_start = now + timedelta(seconds=estimated_wait_seconds)
    target_arrival = consultation_start - timedelta(minutes=ARRIVAL_BUFFER_MINUTES)
    start_walking = target_arrival - timedelta(minutes=patient_travel_minutes)
    def format_time(dt: datetime) -> str:
        return dt.strftime("%I:%M %p").lstrip("0")
    message_ready = queue_position < 50 and estimated_wait_minutes < 480
    return {
        "start_walking_at": format_time(start_walking) if message_ready else "--:--",
        "expected_arrival": format_time(target_arrival) if message_ready else "--:--",
        "estimated_consultation_start": format_time(consultation_start) if message_ready else "--:--",
        "total_wait_minutes": estimated_wait_minutes if message_ready else 0,
        "message_ready": message_ready,
    }

def generate_booking_sms(
    name: str,
    token: str,
    doctor_name: str,
    language: str = "en",
    triage_color: str = "GREEN",
    queue_position: Optional[int] = None,
    avg_consult_seconds: int = 300
) -> str:
    lang_name = LANG_MAP.get(language, "English")
    time_info = {}
    if queue_position is not None and queue_position >= 0:
        time_info = calculate_arrival_time(
            queue_position=queue_position,
            avg_consultation_seconds=avg_consult_seconds
        )
    components = {
        "greeting": f"Namaste {name}",
        "token_confirm": f"Token {token} confirmed for consultation with {doctor_name}",
        "triage_note": "",
        "travel_instruction": "",
        "time_guidance": "",
        "closing": "Wishing you good health"
    }
    if triage_color == "RED":
        components["triage_note"] = "Priority clinical case—our team is preparing for your arrival"
    elif triage_color == "YELLOW":
        components["triage_note"] = "Urgent evaluation advised—please keep your phone accessible"
    if time_info.get("message_ready") and time_info.get("start_walking_at"):
        components["travel_instruction"] = f"Do not travel yet. Begin your journey at {time_info['start_walking_at']}. Please arrive by {time_info['expected_arrival']}."
    else:
        components["travel_instruction"] = "Please do not travel to the hospital yet. Await our 'Start Walking' SMS notification. This helps conserve your time and daily wages."
    if time_info.get("total_wait_minutes") and time_info["total_wait_minutes"] > 0:
        components["time_guidance"] = f"Estimated wait time: approximately {time_info['total_wait_minutes']} minutes."
    if language == "en":
        message = f"{components['greeting']}. {components['token_confirm']}. {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} Present this token at the entrance. —{doctor_name}"
    elif language == "hi":
        message = f"नमस्ते {name}. टोकन {token} {doctor_name} के साथ परामर्श के लिए पुष्टि किया गया. {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} प्रवेश द्वार पर टोकन प्रस्तुत करें. —{doctor_name}"
    elif language == "te":
        message = f"నమస్తే {name}. టోకెన్ {token} {doctor_name} తో సంప్రదింపుల కోసం ధృవీకరించబడింది. {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} ఎంట్రన్స్ వద్ద టోకెన్ చూపించండి. —{doctor_name}"
    elif language == "ta":
        message = f"வணக்கம் {name}. டோக்கன் {token} {doctor_name} உடன் கலந்தாலோசனைக்கு உறுதி செய்யப்பட்டது. {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} நுழைவாயிலில் டோக்கனை காட்டவும். —{doctor_name}"
    elif language == "bn":
        message = f"নমস্কার {name}. টোকেন {token} {doctor_name} এর সাথে পরামর্শের জন্য নিশ্চিত করা হয়েছে। {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} প্রবেশদ্বারে টোকেন দেখান। —{doctor_name}"
    elif language == "mr":
        message = f"नमस्कार {name}. टोकन {token} {doctor_name} सह सल्लामसलतीसाठी निश्चित केले आहे. {components['triage_note']} {components['travel_instruction']} {components['time_guidance']} प्रवेशद्वारावर टोकन दाखवा. —{doctor_name}"
    else:
        message = f"{components['greeting']}. {components['token_confirm']}. {components['travel_instruction']} —{doctor_name}"
    if (_groq_client or _gemini_model) and len(message) > SMS_SAFE_CHARS:
        prompt = f"""Refine this clinical SMS to under {SMS_SAFE_CHARS} characters while preserving critical information:
- Patient: {name}
- Token: {token}
- Physician: {doctor_name}
- Essential instruction: Do not travel yet
- Start walking time (if applicable)

Original: "{message}"

Return ONLY the refined SMS text—no quotes, no explanation."""
        refined = _call_llm_with_fallback(prompt, temperature=0.1, max_tokens=200)
        if refined and len(refined) <= SMS_MAX_CHARS:
            message = refined.strip()
    if len(message) > SMS_MAX_CHARS:
        message = message[:SMS_MAX_CHARS-3] + "..."
    logger.info(f"Generated booking SMS ({language}): {message[:100]}...")
    return message

def generate_walking_sms(
    doctor_name: str,
    token: str,
    language: str = "en",
    patient_name: Optional[str] = None,
    estimated_consult_min: int = 10
) -> str:
    name_part = f"{patient_name}, " if patient_name else ""
    base_templates = {
        "en": f"{name_part}Token {token}: Please proceed to {doctor_name}'s consultation room now. Arrive within {AVG_WALKING_TIME_MINUTES} minutes. Present token at entrance. Estimated consultation: {estimated_consult_min} minutes. —Hospital",
        "hi": f"{name_part}टोकन {token}: कृपया {doctor_name} के परामर्श कक्ष की ओर अभी चलें. {AVG_WALKING_TIME_MINUTES} मिनट में पहुँचें. प्रवेश पर टोकन प्रस्तुत करें. अनुमानित परामर्श समय: {estimated_consult_min} मिनट. —अस्पताल",
        "te": f"{name_part}టోకెన్ {token}: {doctor_name} సంప్రదింపుల గది వైపు దయచేసి ఇప్పుడే బయలుదేరండి. {AVG_WALKING_TIME_MINUTES} నిమిషాల్లో చేరండి. ఎంట్రన్స్ వద్ద టోకెన్ చూపించండి. అంచనా సంప్రదింపు సమయం: {estimated_consult_min} నిమిషాలు. —ఆసుపత్రి",
        "ta": f"{name_part}டோக்கன் {token}: {doctor_name} கலந்தாலோசனை அறைக்கு தயவுசெய்து இப்போதே புறப்படவும். {AVG_WALKING_TIME_MINUTES} நிமிடங்களில் அடையவும். நுழைவாயிலில் டோக்கனை காட்டவும். மதிப்பிடப்பட்ட கலந்தாலோசனை நேரம்: {estimated_consult_min} நிமிடங்கள். —மருத்துவமனை",
        "bn": f"{name_part}টোকেন {token}: {doctor_name} এর পরামর্শ কক্ষের দিকে দয়া করে এখনই রওনা দিন. {AVG_WALKING_TIME_MINUTES} মিনিটের মধ্যে পৌঁছান. প্রবেশদ্বারে টোকেন দেখান. আনুমানিক পরামর্শ সময়: {estimated_consult_min} মিনিট. —হাসপাতাল",
        "mr": f"{name_part}टोकन {token}: {doctor_name} च्या सल्लामसलत खोलीकडे दया करून आताच निघा. {AVG_WALKING_TIME_MINUTES} मिनिटांत पोहोचा. प्रवेशद्वारावर टोकन दाखवा. अंदाजित सल्लामसलत वेळ: {estimated_consult_min} मिनिटे. —रुग्णालय"
    }
    message = base_templates.get(language, base_templates["en"])
    if (_groq_client or _gemini_model) and len(message) > SMS_SAFE_CHARS:
        prompt = f"""Make this clinical 'Start Walking' SMS concise (<{SMS_SAFE_CHARS} chars) while maintaining urgency and clarity:
"{message}"
Return ONLY the SMS text."""
        refined = _call_llm_with_fallback(prompt, temperature=0, max_tokens=150)
        if refined:
            message = refined.strip()
    return message[:SMS_MAX_CHARS]

def generate_status_sms(
    token: str,
    status: str,
    wait_minutes: int,
    language: str = "en",
    patients_ahead: int = 0,
    triage_color: str = "GREEN"
) -> str:
    status_labels = {
        "en": {"WAITING": "awaiting your turn", "CALLED": "please proceed to consultation room", "IN_ROOM": "currently in consultation"},
        "hi": {"WAITING": "आपकी बारी की प्रतीक्षा में", "CALLED": "कृपया परामर्श कक्ष में जाएं", "IN_ROOM": "परामर्श चल रहा है"},
        "te": {"WAITING": "మీ వంతు కోసం వేచి ఉంది", "CALLED": "దయచేసి సంప్రదింపుల గదికి వెళ్ళండి", "IN_ROOM": "సంప్రదింపులు జరుగుతున్నాయి"},
        "ta": {"WAITING": "உங்கள் முறைக்காக காத்திருக்கிறது", "CALLED": "தயவுசெய்து கலந்தாலோசனை அறைக்கு செல்லவும்", "IN_ROOM": "கலந்தாலோசனை நடைபெறுகிறது"},
        "bn": {"WAITING": "আপনার পালা জন্য অপেক্ষা করছে", "CALLED": "দয়া করে পরামর্শ কক্ষে যান", "IN_ROOM": "পরামর্শ চলছে"},
        "mr": {"WAITING": "तुमची पाळीची प्रतीक्षा", "CALLED": "कृपया सल्लामसलत खोलीत जा", "IN_ROOM": "सल्लामसलत सुरू आहे"}
    }
    labels = status_labels.get(language, status_labels["en"])
    status_text = labels.get(status, status.lower())
    if language == "en":
        priority = "PRIORITY " if triage_color == "RED" else ""
        message = f"Token {token}: {priority}{status_text}. Patients ahead: {patients_ahead}. Estimated wait: {wait_minutes} min. Please keep your phone nearby for updates."
    elif language == "hi":
        message = f"टोकन {token}: {status_text}. आगे मरीज: {patients_ahead}. अनुमानित प्रतीक्षा: {wait_minutes} मिनट. अपडेट के लिए फोन पास रखें."
    elif language == "te":
        message = f"టోకెన్ {token}: {status_text}. ముందు రోగులు: {patients_ahead}. అంచనా వేచి: {wait_minutes} నిమి. అప్డేట్ల కోసం ఫోన్ దగ్గర ఉంచండి."
    elif language == "ta":
        message = f"டோக்கன் {token}: {status_text}. முன் நோயாளிகள்: {patients_ahead}. மதிப்பிடப்பட்ட நேரம்: {wait_minutes} நிமி. புதுப்பிப்புகளுக்கு தொலைபேசி அருகில் வைக்கவும்."
    elif language == "bn":
        message = f"টোকেন {token}: {status_text}. সামনে রোগী: {patients_ahead}. আনুমানিক অপেক্ষা: {wait_minutes} মিনিট. আপডেটের জন্য ফোন কাছে রাখুন."
    elif language == "mr":
        message = f"टोकन {token}: {status_text}. पुढील रुग्ण: {patients_ahead}. अंदाजित प्रतीक्षा: {wait_minutes} मिनिटे. अपडेटसाठी फोन जवळ ठेवा."
    else:
        message = f"Token {token}: {status_text}. Wait: ~{wait_minutes} min."
    return message[:SMS_MAX_CHARS]

def generate_cutoff_sms(name: str, doctor_name: str, language: str = "en") -> str:
    fallbacks = {
        "en": f"{name}, {doctor_name}'s consultation slots are fully scheduled today. To avoid unnecessary travel and preserve your daily wages, we advise not visiting today. Please try again tomorrow after 8 AM. Your health matters to us. —Smart OPD",
        "hi": f"{name}, {doctor_name} के परामर्श स्लॉट आज पूर्णतः बुक हैं. अनावश्यक यात्रा और मजदूरी हानि से बचने के लिए, कृपया आज न आएं. कल सुबह 8 बजे के बाद पुनः प्रयास करें. आपका स्वास्थ्य हमारे लिए महत्वपूर्ण है. —स्मार्ट OPD",
        "te": f"{name}, {doctor_name} సంప్రదింపు స్లాట్లు ఇవాళ పూర్తిగా బుక్ అయ్యాయి. అనవసరమైన ప్రయాణం మరియు కూలీ నష్టం నుండి రక్షించడానికి, దయచేసి ఇవాళ రావద్దు. రేపు ఉదయం 8 గంటల తర్వాత మళ్లీ ప్రయత్నించండి. మీ ఆరోగ్యం మాకు ముఖ్యం. —స్మార్ట్ OPD",
        "ta": f"{name}, {doctor_name} கலந்தாலோசனை ஸ்லாட்டுகள் இன்று முழுமையாக பதிவு செய்யப்பட்டுள்ளன. தேவையற்ற பயணம் மற்றும் கூலி இழப்பிலிருந்து பாதுகாக்க, தயவுசெய்து இன்று வரவேண்டாம். நாளை காலை 8 மணிக்குப் பிறகு மீண்டும் முயற்சிக்கவும். உங்கள் ஆரோக்கியம் எங்களுக்கு முக்கியம். —ஸ்மார்ட் OPD",
        "bn": f"{name}, {doctor_name} এর পরামর্শ স্লট আজ সম্পূর্ণ বুক করা হয়েছে. অপ্রয়োজনীয় ভ্রমণ ও মজুরি ক্ষতি এড়াতে, অনুগ্রহ করে আজ আসবেন না. কাল সকাল ৮টার পরে আবার চেষ্টা করুন. আপনার স্বাস্থ্য আমাদের কাছে গুরুত্বপূর্ণ. —স্মার্ট OPD",
        "mr": f"{name}, {doctor_name} च्या सल्लामसलत स्लॉट आज पूर्णपणे बुक आहेत. अनावश्यक प्रवास आणि मजुरी नुकसान टाळण्यासाठी, कृपया आज येऊ नका. उद्या सकाळी ८ वाजल्यानंतर पुन्हा प्रयत्न करा. तुमचे आरोग्य आमच्यासाठी महत्त्वाचे आहे. —स्मार्ट OPD"
    }
    message = fallbacks.get(language, fallbacks["en"])
    if _groq_client or _gemini_model:
        prompt = f"""Refine this clinical capacity notification to be more empathetic while staying under {SMS_SAFE_CHARS} characters:
"{message}"
Key elements: 1) Slots fully booked, 2) Avoid travel today (protect wages), 3) Retry tomorrow morning, 4) Compassionate, professional tone.
Return ONLY the SMS text."""
        refined = _call_llm_with_fallback(prompt, temperature=0.2, max_tokens=200)
        if refined and len(refined) <= SMS_MAX_CHARS and _validate_multilingual_text(refined, language):
            message = refined.strip()
    return message[:SMS_MAX_CHARS]

def generate_emergency_message(language: str = "en", pause_minutes: int = 15, doctor_name: str = "Doctor") -> str:
    templates = {
        "en": f"CLINICAL ALERT: {doctor_name} is managing a critical emergency case. Consultation queue temporarily paused for approximately {pause_minutes} minutes. Please remain within hospital premises. We will provide updates shortly. Thank you for your patience and understanding. —Smart OPD",
        "hi": f"चिकित्सा अलर्ट: {doctor_name} एक गंभीर आपातकालीन मामले का प्रबंधन कर रहे हैं. परामर्श क्यू अस्थायी रूप से लगभग {pause_minutes} मिनट के लिए रोक दी गई है. कृपया अस्पताल परिसर में ही बने रहें. हम शीघ्र ही अपडेट प्रदान करेंगे. आपके धैर्य और समझ के लिए धन्यवाद. —स्मार्ट OPD",
        "te": f"క్లినికల్ అలర్ట్: {doctor_name} ఒక క్లిష్ట అత్యవసర కేసును నిర్వహిస్తున్నారు. సంప్రదింపుల క్యూ సుమారు {pause_minutes} నిమిషాల పాటు అస్థిరంగా నిలిపివేయబడింది. దయచేసి ఆసుపత్రి ప్రాంగణంలోనే ఉండండి. మేము త్వరలో అప్డేట్లు అందిస్తాము. మీ ఓపిక మరియు అవగాహనకు ధన్యవాదాలు. —స్మార్ట్ OPD",
        "ta": f"கிளினிக்கல் அலர்ட்: {doctor_name} ஒரு முக்கிய அவசர வழக்கை கையாளுகிறார். கலந்தாலோசனை வரிசை தற்காலிகமாக சுமார் {pause_minutes} நிமிடங்களுக்கு நிறுத்தப்பட்டுள்ளது. தயவுசெய்து மருத்துவமனை வளாகத்திலேயே இருங்கள். விரைவில் புதுப்பிப்புகளை வழங்குவோம். உங்கள் பொறுமை மற்றும் புரிதலுக்கு நன்றி. —ஸ்மார்ட் OPD",
        "bn": f"ক্লিনিক্যাল অ্যালার্ট: {doctor_name} একটি গুরুতর জরুরি কেস পরিচালনা করছেন। পরামর্শ ক্যু অস্থায়ীভাবে প্রায় {pause_minutes} মিনিটের জন্য বিরতি। অনুগ্রহ করে হাসপাতাল প্রাঙ্গনেই থাকুন। আমরা শীঘ্রই আপডেট প্রদান করব। আপনার ধৈর্য ও বোঝাপড়ার জন্য ধন্যবাদ। —স্মার্ট OPD",
        "mr": f"क्लिनिकल अलर्ट: {doctor_name} एक गंभीर आपत्कालीन केस हाताळत आहेत. सल्लामसलत क्यू अस्थायीपणे सुमारे {pause_minutes} मिनिटांसाठी थांबवली आहे. कृपया रुग्णालय आवारातच रहा. आम्ही लवकरच अपडेट्स प्रदान करू. तुमच्या धैर्य आणि समजूतदारपणाबद्दल धन्यवाद. —स्मार्ट OPD"
    }
    message = templates.get(language, templates["en"])
    return message[:SMS_MAX_CHARS]

def generate_complexity_warning(
    patient_name: str,
    elapsed_minutes: int,
    avg_minutes: int,
    language: str = "en"
) -> str:
    fallbacks = {
        "en": f"{patient_name}: Consultation duration {elapsed_minutes} min (avg: {avg_minutes} min). Clinical consideration: request senior review, order pending diagnostics, or prepare concise handoff summary.",
        "hi": f"{patient_name}: परामर्श अवधि {elapsed_minutes} मिनट (औसत: {avg_minutes} मिनट). चिकित्सा विचार: वरिष्ठ समीक्षा अनुरोध करें, लंबित डायग्नोस्टिक्स ऑर्डर करें, या संक्षिप्त हैंडऑफ सारांश तैयार करें.",
        "te": f"{patient_name}: సంప్రదింపుల కాలం {elapsed_minutes} ని (సగటు: {avg_minutes} ని). క్లినికల్ పరిశీలన: సీనియర్ రివ్యూ కోరండి, పెండింగ్ డయాగ్నోస్టిక్స్ ఆర్డర్ చేయండి, లేదా సంక్షిప్త హ్యాండఆఫ్ సారాంశం సిద్ధం చేయండి.",
        "ta": f"{patient_name}: கலந்தாலோசனை காலம் {elapsed_minutes} நி (சராசரி: {avg_minutes} நி). கிளினிக்கல் கருத்தில்: மூத்த மதிப்பாய்வு கோருங்கள், நிலுவை டயக்னோஸ்டிக்ஸ் ஆர்டர் செய்யுங்கள், அல்லது சுருக்கமான ஹேண்ட்ஆஃப் சுருக்கம் தயாரிக்கவும்.",
        "bn": f"{patient_name}: পরামর্শের সময় {elapsed_minutes} মিনিট (গড়: {avg_minutes} মিনিট). ক্লিনিক্যাল বিবেচনা: সিনিয়র রিভিউ অনুরোধ করুন, পেন্ডিং ডায়াগনোস্টিক্স অর্ডার করুন, বা সংক্ষিপ্ত হ্যান্ডঅফ সারাংশ প্রস্তুত করুন.",
        "mr": f"{patient_name}: सल्लामसलत कालावधी {elapsed_minutes} मि (सरासरी: {avg_minutes} मि). क्लिनिकल विचार: वरिष्ठ समीक्षा विनंती करा, प्रलंबित डायग्नोस्टिक्स ऑर्डर करा, किंवा संक्षिप्त हँडऑफ सारांश तयार करा."
    }
    if not patient_name or (_groq_client is None and _gemini_model is None):
        return fallbacks.get(language, fallbacks["en"])
    lang_name = LANG_MAP.get(language, "English")
    prompt = f"""Clinical decision support note ({lang_name}):
Patient {patient_name} consultation: {elapsed_minutes} minutes elapsed (department average: {avg_minutes} minutes).
Provide ONE concise, clinically actionable suggestion (max 120 characters) to assist the treating physician:
- Request senior physician review?
- Order specific pending diagnostic tests?
- Prepare brief handoff summary for continuity?
- Other immediate clinical step?
Return ONLY the suggestion text—no labels, no punctuation ending."""
    response = _call_llm_with_fallback(prompt, temperature=0.15, max_tokens=100)
    if response and len(response.strip()) <= 150:
        suggestion = response.strip().rstrip('.,;:!')
        if language == "en" or _validate_multilingual_text(suggestion, language):
            return f"{patient_name}: {suggestion}"
    return fallbacks.get(language, fallbacks["en"])

def analyze_symptom_cluster(symptoms_list: List[str]) -> Dict[str, Any]:
    default = {"alert": False}
    if not symptoms_list or len(symptoms_list) < MIN_CLUSTER_SIZE:
        return default
    clean_symptoms = [s.strip() for s in symptoms_list if s and len(s.strip()) > 3]
    if len(clean_symptoms) < MIN_CLUSTER_SIZE:
        return default
    disease_keywords = {
        "Dengue Fever": ["fever", "body pain", "joint pain", "rash", "bone pain", "बुखार", "शरीर दर्द", "जोड़"],
        "Viral Fever": ["fever", "sore throat", "cough", "cold", "body ache", "बुखार", "गले में दर्द", "खांसी"],
        "Cholera": ["diarrhea", "vomiting", "dehydration", "watery stool", "दस्त", "उल्टी", "पानी जैसा"],
        "Influenza": ["fever", "cough", "body ache", "fatigue", "headache", "बुखार", "खांसी", "थकान"],
        "Typhoid": ["fever", "stomach pain", "headache", "weakness", "बुखार", "पेट दर्द", "कमजोरी"]
    }
    symptom_text = " ".join(clean_symptoms).lower()
    matches = {}
    for disease, keywords in disease_keywords.items():
        count = sum(1 for kw in keywords if kw.lower() in symptom_text)
        if count >= 2:
            matches[disease] = count
    if not matches:
        return _ai_analyze_cluster(clean_symptoms)
    top_disease = max(matches, key=matches.get)
    match_count = matches[top_disease]
    lang_name = LANG_MAP.get("en", "English")
    prompt = f"""You are a public health epidemiologist analyzing OPD surveillance data from India.
Recent patient presentations (last 2 hours, {len(clean_symptoms)} cases):
{json.dumps(clean_symptoms[:20], ensure_ascii=False)}
Preliminary keyword analysis suggests: {top_disease} ({match_count} keyword matches)
Task: Assess outbreak likelihood and provide structured clinical assessment.
Return ONLY valid JSON with these exact keys:
{{
  "alert": boolean,
  "suspected_disease": "{top_disease}" or null if clinical uncertainty exists,
  "confidence": float 0.0-1.0 (apply conservative epidemiological judgment),
  "match_count": integer (number of clinically supporting cases),
  "trigger_symptoms": "comma-separated key clinical indicators that triggered alert"
}}
Epidemiological guidelines:
- alert=true ONLY if confidence >= {CONFIDENCE_THRESHOLD}
- Prioritize specificity: false positives consume public health resources
- match_count must reflect actual clinically supporting cases
- trigger_symptoms: 3-5 most discriminative clinical indicators
Example: {{"alert": true, "suspected_disease": "Dengue Fever", "confidence": 0.78, "match_count": 12, "trigger_symptoms": "high fever, severe arthralgia, maculopapular rash"}}"""
    response = _call_llm_with_fallback(prompt, temperature=0.1, max_tokens=400)
    if response:
        data = _extract_json(response)
        if (isinstance(data.get("alert"), bool) and
            "suspected_disease" in data and
            isinstance(data.get("confidence"), (int, float)) and
            0 <= data["confidence"] <= 1 and
            isinstance(data.get("match_count"), int)):
            if data["alert"] and data["confidence"] >= CONFIDENCE_THRESHOLD:
                logger.info(f"EPIDEMIC ALERT: {data['suspected_disease']} (confidence: {data['confidence']:.0%}, cases: {data['match_count']})")
            return data
    confidence = min(0.5 + (match_count * 0.1), 0.95)
    trigger_syms = [kw for kw in disease_keywords[top_disease] if kw.lower() in symptom_text][:5]
    return {
        "alert": confidence >= CONFIDENCE_THRESHOLD,
        "suspected_disease": top_disease,
        "confidence": round(confidence, 2),
        "match_count": match_count,
        "trigger_symptoms": ", ".join(trigger_syms)
    }

def _ai_analyze_cluster(symptoms: List[str]) -> Dict[str, Any]:
    if len(symptoms) < MIN_CLUSTER_SIZE:
        return {"alert": False}
    prompt = f"""You are a public health epidemiologist analyzing symptom surveillance from an Indian hospital OPD.
Recent presentations ({len(symptoms)} patients, last 2 hours):
{json.dumps(symptoms, ensure_ascii=False)}
Task: Detect if these symptoms suggest a potential infectious disease cluster requiring public health intervention.
Return ONLY valid JSON:
{{
  "alert": boolean (true only if clear epidemiological cluster pattern detected),
  "suspected_disease": "string" or null,
  "confidence": float 0.0-1.0 (apply conservative epidemiological judgment),
  "match_count": integer (number of cases supporting the pattern),
  "trigger_symptoms": "comma-separated key clinical indicators"
}}
Critical epidemiological principles:
- alert=true ONLY if confidence >= {CONFIDENCE_THRESHOLD}
- Prefer false negative over false positive (avoid unnecessary public alarm)
- match_count must be a realistic subset of {len(symptoms)} total cases
- If clinical uncertainty exists, return {{"alert": false}}
Example conservative response:
{{"alert": false, "suspected_disease": null, "confidence": 0.4, "match_count": 0, "trigger_symptoms": ""}}"""
    response = _call_llm_with_fallback(prompt, temperature=0.05, max_tokens=400)
    if response:
        data = _extract_json(response)
        if (isinstance(data.get("alert"), bool) and
            "suspected_disease" in data and
            isinstance(data.get("confidence"), (int, float))):
            return data
    return {"alert": False}

def parse_delay_from_reply(reply_text: str, language: str = "en") -> Dict[str, Any]:
    default = {"intent": "UNKNOWN", "delay_minutes": 0}
    if not reply_text or not reply_text.strip():
        return default
    reply_lower = reply_text.lower().strip()
    cancel_keywords = ["cancel", "not coming", "can't make", "रद्द", "नहीं आ सकता", "రద్దు", "வர முடியாது", "বাতিল", "रद्द"]
    if any(kw in reply_lower for kw in cancel_keywords):
        return {"intent": "CANCEL", "delay_minutes": 0}
    delay_match = re.search(r'(\d+)\s*(min|minute|मिनट|నిమి|நிமி|মিনিট|मिनिट)?', reply_lower)
    delay_minutes = int(delay_match.group(1)) if delay_match else 0
    late_keywords = ["late", "delay", "थोड़ी देर", "देरी", "లేట్", "தாமதம்", "বিলম্ব", "उशीर"]
    if any(kw in reply_lower for kw in late_keywords) or delay_minutes > 0:
        return {"intent": "LATE", "delay_minutes": min(delay_minutes, 120)}
    coming_keywords = ["coming", "on way", "रहा हूं", "आ रहा", "వస్తున్నా", "வருகிறேன்", "আসছি", "येतोय"]
    if any(kw in reply_lower for kw in coming_keywords):
        return {"intent": "COMING", "delay_minutes": 0}
    if (_groq_client or _gemini_model) and len(reply_text) > 10:
        lang_name = LANG_MAP.get(language, "English")
        prompt = f"""Parse this patient SMS reply ({lang_name}): "{reply_text}"
Return ONLY JSON with these exact keys:
{{"intent": "COMING" or "LATE" or "CANCEL" or "UNKNOWN", "delay_minutes": integer}}
Clinical parsing rules:
- intent="CANCEL" if patient indicates they will not attend
- intent="LATE" if delayed (extract minutes, default 15 if mentioned but not specified)
- intent="COMING" if en route with no anticipated delay
- intent="UNKNOWN" if clinical intent unclear
- delay_minutes: 0 if not mentioned, else extracted number (max 120)
NO other text, NO markdown."""
        response = _call_llm_with_fallback(prompt, temperature=0, max_tokens=100)
        if response:
            data = _extract_json(response)
            if data.get("intent") in ["COMING", "LATE", "CANCEL", "UNKNOWN"] and isinstance(data.get("delay_minutes"), int):
                data["delay_minutes"] = max(0, min(data["delay_minutes"], 120))
                return data
    return default

def check_ai_health() -> Dict[str, Any]:
    result = {
        "status": "unavailable",
        "groq_available": _groq_client is not None,
        "gemini_available": _gemini_model is not None,
        "latency_ms": None,
        "capabilities": {
            "triage": False,
            "sms_generation": False,
            "epidemic_detection": False
        }
    }
    if _groq_client is None and _gemini_model is None:
        return result
    try:
        start = time.time()
        test_prompt = "Respond with ONLY: {\"ok\": true}"
        response = _call_llm_with_fallback(test_prompt, temperature=0, max_tokens=20, max_retries=1)
        latency = (time.time() - start) * 1000
        result["latency_ms"] = round(latency, 1)
        result["status"] = "healthy" if response and '"ok": true' in response else "degraded"
        result["capabilities"] = {
            "triage": True,
            "sms_generation": True,
            "epidemic_detection": True
        }
        return result
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        return result

def get_supported_languages() -> List[Dict[str, str]]:
    return [
        {"code": code, "name": name, "native": name}
        for code, name in LANG_MAP.items()
    ]

def format_sms_for_provider(message: str, phone: str, sender_id: str = "SMRTOP") -> Dict[str, Any]:
    if len(message) > SMS_MAX_CHARS:
        message = message[:SMS_MAX_CHARS-3] + "..."
    is_unicode = any(ord(c) > 127 for c in message)
    encoding = "unicode" if is_unicode else "english"
    chars_per_part = 70 if is_unicode else 160
    parts = (len(message) + chars_per_part - 1) // chars_per_part
    return {
        "to": phone,
        "message": message,
        "sender_id": sender_id,
        "encoding": encoding,
        "parts": parts,
        "length": len(message),
        "cost_estimate": parts * (0.04 if is_unicode else 0.02)
    }

def log_ai_interaction(
    function_name: str,
    input_summary: str,
    output_summary: str,
    latency_ms: Optional[float] = None,
    success: bool = True
):
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "function": function_name,
        "input": input_summary[:200],
        "output": output_summary[:200],
        "latency_ms": latency_ms,
        "success": success,
        "groq_available": _groq_client is not None,
        "gemini_available": _gemini_model is not None
    }
    if success:
        logger.info(f"AI✓ {function_name}: {input_summary[:50]}...")
    else:
        logger.warning(f"AI✗ {function_name}: {input_summary[:50]}... -> fallback used")