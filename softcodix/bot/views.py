import os
import json
import requests
import concurrent.futures
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from .models import PageContent
import threading 

SERVICE_QUESTIONS = {
    "website": [
        "What type of website do you need? (Business / E-commerce / Portfolio / Blog )",
        "Approximately how many pages do you need?",
        "What is your budget range?"
    ],
    "mobile-app": [
        "Do you need Android, iOS, or both?",
        "What is the purpose of the app? (Business , E-commerce , Social , etc.)",
        "How many users are expected?",
        "Any special features needed? (Push notifications, payment, etc.)",
        "What is your budget and timeline?"
    ],
    "marketing": [
        "What type of marketing services do you need? (Social Media, SEO, Paid Ads, Email , etc.)",
        "Which platforms would you like to focus on? (Facebook , Instagram , Google, TikTok, etc.)",
        "What is your approximate monthly marketing budget?",
        "Who is your target audience? (Age, location, interests, profession, etc.)",
        "Are there any ongoing marketing campaigns? If yes, could you share a brief overview?"
    ],
    "chatbot": [
        "Which platform do you need the chatbot for? (Website , WhatsApp , Facebook)",
        "What is the purpose of the chatbot? (Customer support, lead generation, AI-powered assistant)",
        "In which language should the chatbot reply? (English, Urdu, both)",
        "Do you need an AI-powered chatbot or a simple rule-based one?"
    ],
    "design": [
        "What type of design do you need? (Logo, Branding, Social Media Posts, UI/UX, Print)",
        "If you need a logo, what is the business name and is there a tagline?",
        "In which file format do you need the final design? (PNG, PSD, AI, PDF)",
        "What is your budget and timeline?"
    ]
}

SERVICE_KEYWORDS = {
    "website": ["website", "web", "site", "webpage"],
    "mobile-app": ["app", "mobile", "application", "android", "ios", "apk"],
    "marketing": ["marketing", "ads", "seo", "social media", "facebook ads", "instagram ads"],
    "chatbot": ["chatbot", "bot", "chat bot", "whatsapp bot"],
    "design": ["design", "logo", "graphics", "branding", "ui", "ux"]
}

def send_lead_email_async(lead_data):
    """Send email in background thread"""
    thread = threading.Thread(target=send_lead_email, args=(lead_data,))
    thread.daemon = True  # Thread will die when main program exits
    thread.start()
    print("[Email] ✅ Email sending started in background")

def send_lead_email(lead_data):
    """Send lead details via email"""
    try:
        service = lead_data.get('service', 'N/A')
        name = lead_data.get('name', 'N/A')
        phone = lead_data.get('phone', 'N/A')
        email = lead_data.get('email', 'N/A')
        answers = lead_data.get('answers', {})
        
        print(f"[Email] Preparing to send lead email...")
        print(f"[Email] Service: {service}")
        print(f"[Email] Name: {name}")
        print(f"[Email] Phone: {phone}")
        print(f"[Email] Email: {email}")
        print(f"[Email] Answers: {answers}")
        
        if not name or name == 'N/A':
            print("[Email] ⚠️ WARNING: Name is empty!")
        if not phone or phone == 'N/A':
            print("[Email] ⚠️ WARNING: Phone is empty!")
        if not email or email == 'N/A':
            print("[Email] ⚠️ WARNING: Email is empty!")
        
        company_email_body = f"""
🎉 New Lead from Chatbot!

📋 Service Interested: {service.upper()}

👤 Contact Details:
- Name: {name}
- Phone: {phone}
- Email: {email}

💬 Responses:
"""
        
        for question, answer in answers.items():
            company_email_body += f"\nQ: {question}\nA: {answer}\n"
        
        company_email_body += "\n---\nPlease contact this lead ASAP!"
        
        user_email_body = f"""
Hi {name},

Thank you for your interest in our {service.replace('-', ' ').upper()} services! 🎉

We have received your inquiry and our team will contact you within 24 hours.

Your Details:
- Service: {service.upper()}
- Phone: {phone}
- Email: {email}

If you have any urgent questions, feel free to call us at 02138899998 or WhatsApp at 03218795135.

Best Regards,
Softcodix Team
"""
        
        print(f"[Email] Sending to company: {settings.LEAD_EMAIL}")
        print(f"[Email] Sending to user: {email}")
        
        send_mail(
            subject=f'New {service.upper()} Lead - {name}',
            message=company_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.LEAD_EMAIL],
            fail_silently=False,
        )
        
        send_mail(
            subject=f'Thank You for Contacting Softcodix - {service.upper()}',
            message=user_email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        print(f"[Email] ✅ Both emails sent successfully!")
        return True
        
    except Exception as e:
        print(f"[Email] ❌ Error: {str(e)}")
        return False


def get_active_service_context(output_contexts):
    """Extract active service context and its parameters"""
    for context in output_contexts:
        context_name = context.get("name", "")
        for service in ["website", "mobile-app", "marketing", "chatbot", "design"]:
            if f"{service}-context" in context_name:
                params = context.get("parameters", {})
                print(f"[Context] Found active: {service}-context")
                print(f"[Context] Parameters: {params}")
                return service, params
    return None, {}


def has_any_active_service_context(output_contexts):
    """Check if ANY service context is active"""
    for context in output_contexts:
        context_name = context.get("name", "")
        for service in ["website", "mobile-app", "marketing", "chatbot", "design"]:
            if f"{service}-context" in context_name:
                lifespan = context.get("lifespanCount", 0)
                if lifespan > 0:
                    return True
    return False


def detect_service_from_query(query):
    """Detect service intent from user query using keywords"""
    query_lower = query.lower()
    
    for service, keywords in SERVICE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in query_lower:
                print(f"[Keyword Detection] Found '{keyword}' -> Service: {service}")
                return service
    
    return None


def query_gemini_softcodix(user_query, website_content, services, timeout=4):
    """Ask Gemini to answer user query based on Softcodix website data"""
    try:
        prompt = f"""
        You are a helpful assistant for **Softcodix**.
        You are a friendly **sales agent** for Softcodix.

        📝 RULES:
        - Always reply in same language as user query.
        - If language is "urdu", reply in **Roman Urdu** (English alphabets only).
        - If language is "English", reply in **English**.
        - Keep answers short (3-5 lines).
        - Be professional but friendly, like chatting on WhatsApp.
        - Do NOT always start with greetings.
        - If query is about services, explain briefly with 2-3 bullet points.
        - End with a small call-to-action.

        Company Info:
        {website_content}

        Our Services:
        {services}  

        User asked: {user_query}
        """

        GEMINI_API_KEY = getattr(settings, "GEMINI_API_KEY", None)
        if not GEMINI_API_KEY:
            return "⚠️ Gemini API key not configured."

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            return f"⚠️ Gemini error: {response.status_code}"

    except Exception as e:
        return f"⚠️ Gemini exception: {str(e)}"


def query_with_timeout_softcodix(user_query, website_content, services, timeout=4):
    """Run Gemini query but fallback if slow"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(query_gemini_softcodix, user_query, website_content, services, timeout)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return "⏳ Server busy hai, please try again shortly."


def smart_query_handler_softcodix(user_query):
    """Main Softcodix chatbot handler"""
    db_result = PageContent.objects.filter(content__icontains=user_query)
    if db_result.exists():
        snippet = db_result.first().content[:400]
        return f"🔍 I found this info:\n{snippet}"

    website_content = "Softcodix is an IT solutions company providing AI, automation, and custom development."
    services = "- AI Chatbots\n- Web & Mobile Development\n- Business Automation\n- Cloud & API Integrations"

    return query_with_timeout_softcodix(user_query, website_content, services, timeout=4)


@csrf_exempt
def dialogflow_webhook(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    body = json.loads(request.body.decode("utf-8"))
    user_query = body.get("queryResult", {}).get("queryText", "")
    intent_name = body.get("queryResult", {}).get("intent", {}).get("displayName", "")
    parameters = body.get("queryResult", {}).get("parameters", {})
    output_contexts = body.get("queryResult", {}).get("outputContexts", [])
    session = body.get("session", "")

    print(f"\n{'='*60}")
    print(f"[Webhook] User Query: {user_query}")
    print(f"[Webhook] Intent: {intent_name}")
    print(f"[Webhook] Parameters: {parameters}")
    print(f"[Webhook] Active Contexts: {[c.get('name', '').split('/')[-1] for c in output_contexts]}")
    print(f"{'='*60}\n")

    # Block service-inquiry intents if another service context is already active
    if intent_name in ["website-inquiry", "mobile-app-inquiry", "marketing-inquiry", "chatbot-inquiry", "design-inquiry"]:
        requested_service = intent_name.replace("-inquiry", "")
        active_service, _ = get_active_service_context(output_contexts)
        
        if active_service and active_service != requested_service:
            print(f"[BLOCKED] {intent_name} ignored because {active_service}-context is active")
            print(f"[BLOCKED] Treating as answer to {active_service} question")
            intent_name = "Default Fallback Intent"
        else:
            service = requested_service
            first_question = SERVICE_QUESTIONS[service][0]
            
            print(f"[Service Selected] {service}")
            print(f"[First Question] {first_question}")
            
            return JsonResponse({
                "fulfillmentText": f"Great! Aap {service.replace('-', ' ').upper()} development mein interested hain. ✨\n\nMain kuch quick questions puchna chahta hoon taake hum aapki requirements achhe se samajh sakein.\n\n{first_question}",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/{service}-context",
                        "lifespanCount": 20,
                        "parameters": {
                            "service": service,
                            "question_index": 1,
                            "answers": {}
                        }
                    }
                ]
            })
    
    # Service Questions Intent
    if intent_name == "service-questions":
        print("[service-questions intent triggered]")
        
        active_service, context_params = get_active_service_context(output_contexts)
        
        if not active_service:
            print("[ERROR] No active service context found")
            return JsonResponse({
                "fulfillmentText": "⚠️ Session expired. Please select service again."
            })
        
        service = context_params.get("service", active_service)
        question_index = int(float(context_params.get("question_index", 0)))
        answers = context_params.get("answers", {})
        
        print(f"[Question Flow] Service: {service}, Index: {question_index}")
        
        if question_index > 0 and question_index <= len(SERVICE_QUESTIONS[service]):
            prev_question = SERVICE_QUESTIONS[service][question_index - 1]
            answers[prev_question] = user_query
            print(f"[Answer Stored] {prev_question} = {user_query}")
        
        if question_index < len(SERVICE_QUESTIONS[service]):
            next_question = SERVICE_QUESTIONS[service][question_index]
            print(f"[Next Question] {next_question}")
            
            return JsonResponse({
                "fulfillmentText": next_question,
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/{service}-context",
                        "lifespanCount": 20,
                        "parameters": {
                            "service": service,
                            "question_index": question_index + 1,
                            "answers": answers
                        }
                    }
                ]
            })
        else:
            print("[Questions Complete] Moving to contact collection")
            
            return JsonResponse({
                "fulfillmentText": "Perfect! 🎯\n\nAb main aapki contact details collect karta hoon taake humari team aapse contact kar sake.\n\nAapka naam kya hai?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "step": "name"
                        }
                    }
                ]
            })

    # Collect Contact Details
    elif intent_name == "collect-contact-details":
        collect_context = None
        for context in output_contexts:
            if "collect-details" in context.get("name", ""):
                collect_context = context
                break
        
        if not collect_context:
            print("[Contact] ❌ No collect-details context found")
            return JsonResponse({
                "fulfillmentText": "⚠️ Session expired. Please start again."
            })
        
        context_params = collect_context.get("parameters", {})
        step = context_params.get("step")
        service = context_params.get("service")
        answers = context_params.get("answers", {})
        
        print(f"[Contact] Step: {step}")
        print(f"[Contact] Service: {service}")
        
        if step == "name":
            name = parameters.get("person", {}).get("name") if isinstance(parameters.get("person"), dict) else parameters.get("person")
            if not name:
                name = user_query.strip()
            
            print(f"[Contact] Name collected: {name}")
            
            return JsonResponse({
                "fulfillmentText": f"Thanks {name}! 😊\n\nAapka phone number kya hai?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "name": name,
                            "step": "phone"
                        }
                    }
                ]
            })
        
        elif step == "phone":
            phone = parameters.get("phone-number")
            if not phone:
                phone = user_query.strip()
            
            print(f"[Contact] Phone collected: {phone}")
            
            return JsonResponse({
                "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
                "outputContexts": [
                    {
                        "name": f"{session}/contexts/collect-details",
                        "lifespanCount": 10,
                        "parameters": {
                            "service": service,
                            "answers": answers,
                            "name": context_params.get("name"),
                            "phone": phone,
                            "step": "email"
                        }
                    }
                ]
            })
        
        elif step == "email":
            email = parameters.get("email")
            if not email:
                email = user_query.strip()
            
            print(f"[Contact] Email collected: {email}")
            
            lead_name = context_params.get("name", "Not provided")
            lead_phone = context_params.get("phone", "Not provided")

            print(f"[Lead Data] Name: {lead_name}")
            print(f"[Lead Data] Phone: {lead_phone}")
            print(f"[Lead Data] Email: {email}")
            
            lead_data = {
                "service": service,
                "name": lead_name,
                "phone": lead_phone,
                "email": email,
                "answers": answers
            }
            
            print(f"[Lead Data] Complete lead: {lead_data}")
            
            # email_sent = send_lead_email(lead_data)
            
            # if email_sent:
            #     return JsonResponse({
            #         "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
            #     })
            # else:
            #     return JsonResponse({
            #         "fulfillmentText": "⚠️ Sorry, kuch technical issue hai. Please try again or call us at 02138899998"
            #     })
            send_lead_email_async(lead_data)

            return JsonResponse({
                "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
            })
            
    # Helpline Intent
    elif intent_name == "helpline":
        return JsonResponse({
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [
                            "📞 Our helpline number is: 02138899998\nFeel free to call us anytime during business hours. We're here to help! 😊"
                        ]
                    }
                },
                {
                    "payload": {
                        "richContent": [
                            [
                                {
                                    "icon": {
                                        "type": "chevron_right",
                                        "color": "#25D366"
                                    },
                                    "text": "📱 WhatsApp",
                                    "type": "button",
                                    "link": "https://wa.me/923151179953"
                                }
                            ]
                        ]
                    }
                }
            ]
        })

    # LLM Query Intent
    elif intent_name == "LLMQueryIntent":
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})

    # Default Fallback Intent
    elif intent_name == "Default Fallback Intent":
        print("[Fallback] Checking for active contexts...")
        
        active_service, context_params = get_active_service_context(output_contexts)
        
        if active_service:
            print(f"[Fallback] User is in {active_service} question flow")
            
            service = context_params.get("service", active_service)
            question_index = int(float(context_params.get("question_index", 0)))
            answers = context_params.get("answers", {})
            
            print(f"[Question Flow] Current index: {question_index}")
            print(f"[Question Flow] Total questions: {len(SERVICE_QUESTIONS[service])}")
            
            if question_index > 0 and question_index <= len(SERVICE_QUESTIONS[service]):
                prev_question = SERVICE_QUESTIONS[service][question_index - 1]
                answers[prev_question] = user_query
                print(f"[Answer Stored] Q{question_index}: {user_query}")
            
            if question_index < len(SERVICE_QUESTIONS[service]):
                next_question = SERVICE_QUESTIONS[service][question_index]
                print(f"[Next Question] {next_question}")
                
                return JsonResponse({
                    "fulfillmentText": next_question,
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/{service}-context",
                            "lifespanCount": 20,
                            "parameters": {
                                "service": service,
                                "question_index": question_index + 1,
                                "answers": answers
                            }
                        }
                    ]
                })
            else:
                print("[Questions Complete] Moving to contact collection")
                
                return JsonResponse({
                    "fulfillmentText": "Perfect! 🎯\n\nAb main aapki contact details collect karta hoon taake humari team aapse contact kar sake.\n\nAapka naam kya hai?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "step": "name"
                            }
                        }
                    ]
                })
        
        # Check if in contact collection flow
        collect_context = None
        for context in output_contexts:
            if "collect-details" in context.get("name", ""):
                collect_context = context
                break
        
        if collect_context:
            print("[Fallback] User is in contact collection flow")
            
            context_params = collect_context.get("parameters", {})
            step = context_params.get("step")
            service = context_params.get("service")
            answers = context_params.get("answers", {})
            
            if not step:
                print("[Fallback] ⚠️ No step found in collect-details context")
                return JsonResponse({
                    "fulfillmentText": "⚠️ Session expired. Please start again."
                })
            
            if step == "name":
                name = user_query.strip()
                print(f"[Contact via Fallback] Name: {name}")
                
                return JsonResponse({
                    "fulfillmentText": f"Thanks {name}! 😊\n\nAapka phone number kya hai?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "name": name,
                                "step": "phone"
                            }
                        }
                    ]
                })
            
            elif step == "phone":
                phone = user_query.strip()
                print(f"[Contact via Fallback] Phone: {phone}")
                
                return JsonResponse({
                    "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "name": context_params.get("name"),
                                "phone": phone,
                                "step": "email"
                            }
                        }
                    ]
                })
            
            elif step == "email":
                email = user_query.strip()
                print(f"[Contact via Fallback] Email: {email}")

                lead_name = context_params.get("name", "Not provided")
                lead_phone = context_params.get("phone", "Not provided")

                print(f"[Lead Data via Fallback] Name: {lead_name}")
                print(f"[Lead Data via Fallback] Phone: {lead_phone}")
                print(f"[Lead Data via Fallback] Email: {email}")

                lead_data = {
                    "service": service,
                    "name": lead_name,
                    "phone": lead_phone,
                    "email": email,
                    "answers": answers
                }
                
                print(f"[Lead Data] {lead_data}")
                
                email_sent = send_lead_email(lead_data)
                
                if email_sent:
                    return JsonResponse({
                        "fulfillmentText": f"Perfect! ✅\n\nThank you {lead_name}! Aapki details successfully submit ho gayi hain.\n\nHumari team 24 hours ke andar aapse contact karegi. 🚀\n\nKya main aur kuch help kar sakta hoon?"
                    })
                else:
                    return JsonResponse({
                        "fulfillmentText": "⚠️ Sorry, kuch technical issue hai. Please try again or call us at 02138899998"
                    })
        
        # Keyword detection only if no service context active
        if not has_any_active_service_context(output_contexts):
            detected_service = detect_service_from_query(user_query)
            
            if detected_service:
                print(f"[Fallback] Detected service from keywords: {detected_service}")
                first_question = SERVICE_QUESTIONS[detected_service][0]
                
                return JsonResponse({
                    "fulfillmentText": f"Great! Aap {detected_service.replace('-', ' ').upper()} development mein interested hain. ✨\n\nMain kuch quick questions puchna chahta hoon taake hum aapki requirements achhe se samajh sakein.\n\n{first_question}",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/{detected_service}-context",
                            "lifespanCount": 20,
                            "parameters": {
                                "service": detected_service,
                                "question_index": 1,
                                "answers": {}
                            }
                        }
                    ]
                })
        else:
            print("[Fallback] Service context active - skipping keyword detection")
        
        # No context - use Gemini
        print("[Fallback] No active context, using Gemini")
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})

    # Unknown Intent
    else:
        print(f"[Unknown Intent] {intent_name}")
        reply = smart_query_handler_softcodix(user_query)
        return JsonResponse({"fulfillmentText": reply})