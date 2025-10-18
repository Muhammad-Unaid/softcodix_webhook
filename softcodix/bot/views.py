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
        "What is your budget range?"
    ],
    "marketing": [
        "What type of marketing services do you need? (Social , SEO, Paid Ads, Email , etc.)",
        "Which platforms would you like to focus on? (Facebook , Instagram , Google, TikTok, etc.)",
        "What is your approximate monthly marketing budget?",
        "Who is your target audience? (Age, location, interests, profession, etc.)",
        "Are there any ongoing marketing campaigns? If yes, could you share a brief overview?"
    ],
    "chatbot": [
        "Which platform do you need the chatbot for? (Website , WhatsApp , Facebook)",
        "What is the purpose of the chatbot? (Customer support, lead generation, AI Assistant)",
        "In which language should the chatbot reply? (English, Urdu, both)",
        "Do you need an AI-powered chatbot or a simple rule-based one?"
    ],
    "design": [
        "What type of design do you need? (Logo, Branding, Social Media Posts, UI/UX, Print)",
        "If you need a logo, what is the business name and is there a tagline?",
        "In which file format do you need the final design? (PNG, PSD, AI, PDF)",
        "What is your budget range?"
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

# def send_lead_email(lead_data):
#     """Send lead details via email"""
#     try:
#         service = lead_data.get('service', 'N/A')
#         name = lead_data.get('name', 'N/A')
#         phone = lead_data.get('phone', 'N/A')
#         email = lead_data.get('email', 'N/A')
#         answers = lead_data.get('answers', {})
        
#         print(f"[Email] Preparing to send lead email...")
#         print(f"[Email] Service: {service}")
#         print(f"[Email] Name: {name}")
#         print(f"[Email] Phone: {phone}")
#         print(f"[Email] Email: {email}")
#         print(f"[Email] Answers: {answers}")
        
#         if not name or name == 'N/A':
#             print("[Email] ⚠️ WARNING: Name is empty!")
#         if not phone or phone == 'N/A':
#             print("[Email] ⚠️ WARNING: Phone is empty!")
#         if not email or email == 'N/A':
#             print("[Email] ⚠️ WARNING: Email is empty!")
        
#         company_email_body = f"""
# 🎉 New Lead from Chatbot!

# 📋 Service Interested: {service.upper()}

# 👤 Contact Details:
# - Name: {name}
# - Phone: {phone}
# - Email: {email}

# 💬 Responses:
# """
        
#         for question, answer in answers.items():
#             company_email_body += f"\nQ: {question}\nA: {answer}\n"
        
#         company_email_body += "\n---\nPlease contact this lead ASAP!"
        
#         user_email_body = f"""
# Hi {name},

# Thank you for your interest in our {service.replace('-', ' ').upper()} services! 🎉

# We have received your inquiry and our team will contact you within 24 hours.

# Your Details:
# - Service: {service.upper()}
# - Phone: {phone}
# - Email: {email}

# If you have any urgent questions, feel free to call us at 02138899998 or WhatsApp at 03218795135.

# Best Regards,
# Softcodix Team
# """
        
#         print(f"[Email] Sending to company: {settings.LEAD_EMAIL}")
#         print(f"[Email] Sending to user: {email}")
        
#         send_mail(
#             subject=f'New {service.upper()} Lead - {name}',
#             message=company_email_body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[settings.LEAD_EMAIL],
#             fail_silently=False,
#         )
        
#         send_mail(
#             subject=f'Thank You for Contacting Softcodix - {service.upper()}',
#             message=user_email_body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[email],
#             fail_silently=False,
#         )
        
#         print(f"[Email] ✅ Both emails sent successfully!")
#         return True
        
#     except Exception as e:
#         print(f"[Email] ❌ Error: {str(e)}")
#         return False

def send_lead_email(lead_data):
    """Send lead details via email with HTML card design"""
    try:
        from django.core.mail import EmailMultiAlternatives
        
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
        print(f"[Email] Full lead_data: {lead_data}")
        
        # ✅ Better validation
        if not name or name == 'N/A' or name.strip() == '':
            print("[Email] ⚠️ WARNING: Name is empty!")
            name = "Guest User"
        if not phone or phone == 'N/A' or phone.strip() == '':
            print("[Email] ⚠️ WARNING: Phone is empty!")
            phone = "Not provided"
        if not email or email == 'N/A' or '@' not in email:
            print("[Email] ⚠️ ERROR: Invalid email!")
            return False
        
        # ✅ Build Q&A HTML
        qa_html = ""
        for question, answer in answers.items():
            qa_html += f"""
            <div style="margin-bottom: 15px; padding: 12px; background: #f8f9fa; border-left: 4px solid #E31E24; border-radius: 4px;">
                <p style="margin: 0 0 8px 0; font-weight: 600; color: #1B2A4A;">❓ {question}</p>
                <p style="margin: 0; color: #333;">✅ {answer}</p>
            </div>
            """
        
        # ✅ Company Email HTML
        company_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.12);">
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); padding: 40px 20px; text-align: center;">
                    <div style="background: white; display: inline-block; padding: 15px 30px; border-radius: 8px;">
                        <h2 style="color: #E31E24; margin: 0;">SOFTCODIX</h2>
                    </div>
                    <h1 style="color: white; margin: 20px 0 0 0; font-size: 28px;">🎉 New Lead Alert!</h1>
                </div>
                
               
                
                <div style="background: linear-gradient(90deg, #E31E24 0%, #C71920 100%); padding: 18px; text-align: center;">
                    <p style="margin: 0; font-size: 20px; font-weight: bold; color: white;">
                        📋 SERVICE: {service.upper().replace('-', ' ')}
                    </p>
                </div>
                
                <div style="padding: 35px 30px;">
                    <h2 style="color: #1B2A4A; border-bottom: 3px solid #E31E24; padding-bottom: 12px;">
                        👤 Contact Information
                    </h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; border: 2px solid #1B2A4A;">
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; width: 40%;">Name:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A;">{name}</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; border-top: 2px solid white;">Phone:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A; border-top: 2px solid #e0e0e0;">{phone}</td>
                        </tr>
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; color: white; font-weight: 700; border-top: 2px solid white;">Email:</td>
                            <td style="padding: 15px; background: white; border-left: 2px solid #1B2A4A; border-top: 2px solid #e0e0e0;">{email}</td>
                        </tr>
                    </table>
                    
                    <h2 style="color: #1B2A4A; border-bottom: 3px solid #E31E24; padding-bottom: 12px;">
                        💬 Requirements
                    </h2>
                    
                    {qa_html}
                    
                </div>
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); color: white; padding: 25px; text-align: center;">
                    <p style="margin: 0 0 12px 0; font-weight: bold; font-size: 18px; color: #E31E24;">⚡ Contact ASAP!</p>
                    <p style="margin: 0; font-size: 15px;">Contact within 24 hours for best conversion 🚀</p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        # ✅ User Email HTML
        user_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f0f2f5;">
            <div style="max-width: 650px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.12);">
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); padding: 40px 20px; text-align: center;">
                    <div style="background: white; display: inline-block; padding: 15px 30px; border-radius: 8px;">
                        <h2 style="color: #E31E24; margin: 0;">SOFTCODIX</h2>
                    </div>
                    <h1 style="color: white; margin: 20px 0 0 0; font-size: 28px;">Thank You! 🎉</h1>
                </div>
                
                <div style="padding: 35px 30px;">
                    <p style="font-size: 18px; color: #1B2A4A; font-weight: 600;">
                        Hi <span style="color: #E31E24;">{name}</span>,
                    </p>
                    
                    <p style="font-size: 16px; color: #333; line-height: 1.8;">
                        Thank you for your interest in our <strong style="color: #1B2A4A;">{service.upper().replace('-', ' ')}</strong> services! 🚀
                    </p>
                    
                    <div style="background: linear-gradient(135deg, #E31E24 0%, #C71920 100%); border-radius: 8px; padding: 20px; margin: 25px 0; text-align: center;">
                        <p style="margin: 0; color: white; font-weight: 700; font-size: 18px;">✅ Inquiry Received!</p>
                    </div>
                    
                    <p style="font-size: 16px; color: #333; line-height: 1.8;">
                        Our team will contact you within <strong style="color: #E31E24;">24 hours</strong>.
                    </p>
                    
                    <h3 style="color: #1B2A4A; margin-top: 30px; border-bottom: 2px solid #E31E24; padding-bottom: 10px;">📞 Need Help?</h3>
                    
                    <table style="width: 100%; margin: 20px 0;">
                        <tr>
                            <td style="padding: 15px; background: #1B2A4A; border-radius: 8px; text-align: center;">
                                <strong style="color: white;">📞 Call: 02138899998</strong>
                            </td>
                        </tr>
                        <tr><td style="height: 12px;"></td></tr>
                        <tr>
                            <td style="padding: 15px; background: #25D366; border-radius: 8px; text-align: center;">
                                <a href="https://wa.me/923218795135" style="color: white; text-decoration: none; font-weight: bold;">
                                    💬 WhatsApp: +92 321 8795135
                                </a>
                            </td>
                        </tr>
                    </table>
                    
                </div>
                
                <div style="background: linear-gradient(135deg, #1B2A4A 0%, #0D1625 100%); color: white; padding: 25px; text-align: center;">
                    <p style="margin: 0; font-weight: bold; color: #E31E24;">SOFTCODIX</p>
                    <p style="margin: 8px 0 0 0; font-size: 14px;">Simplified Digital Solution 🚀</p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        # ✅ Send Company Email
        print(f"[Email] Sending company email to: {settings.LEAD_EMAIL}")
        company_msg = EmailMultiAlternatives(
            subject=f'🎯 New {service.upper()} Lead - {name}',
            body=f"New lead from {name}. Check HTML version.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.LEAD_EMAIL]
        )
        company_msg.attach_alternative(company_html, "text/html")
        company_msg.send()
        print("[Email] ✅ Company email sent!")
        
        # ✅ Send User Email
        print(f"[Email] Sending user email to: {email}")
        user_msg = EmailMultiAlternatives(
            subject=f'✅ Thank You - Softcodix {service.upper()}',
            body=f"Hi {name}, Thank you!",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        user_msg.attach_alternative(user_html, "text/html")
        user_msg.send()
        print("[Email] ✅ User email sent!")
        
        print(f"[Email] ✅ Both emails sent!")
        return True
        
    except Exception as e:
        print(f"[Email] ❌ Error: {str(e)}")
        import traceback
        print(f"[Email] Traceback: {traceback.format_exc()}")
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
            email = user_query.strip()
            # email = parameters.get("email")
            # if not email:
            #     email = user_query.strip()
            
            print(f"[Contact] Email collected: {email}")
            
            # ✅ FIX: Manually extract from parameters FIRST, then fallback to context
            param_name = parameters.get("name", {}).get("name") if isinstance(parameters.get("name"), dict) else parameters.get("name")
            param_phone = parameters.get("phone")
            
                # If parameters are empty, get from context
            lead_name = param_name if param_name else context_params.get("name", "Guest User")
            lead_phone = param_phone if param_phone else context_params.get("phone", "Not provided")
            
                # Clean empty strings
            if not lead_name or lead_name.strip() == '':
                lead_name = "Guest User"
            if not lead_phone or lead_phone.strip() == '':
                lead_phone = "Not provided"
            
            # lead_name = context_params.get("name", "Guest User")
            # lead_phone = context_params.get("phone", "Not provided")

            # print(f"[Lead Data] Name: {lead_name}")
            # print(f"[Lead Data] Phone: {lead_phone}")
            # print(f"[Lead Data] Email: {email}")
            # print(f"[Lead Data via Fallback] Full context_params: {context_params}")  # ✅ ADD THIS
            
            print(f"[Lead Data] Name from params: {param_name}")
            print(f"[Lead Data] Name from context: {context_params.get('name')}")
            print(f"[Lead Data] Final Name: {lead_name}")
            print(f"[Lead Data] Phone from params: {param_phone}")
            print(f"[Lead Data] Phone from context: {context_params.get('phone')}")
            print(f"[Lead Data] Final Phone: {lead_phone}")
            print(f"[Lead Data] Email: {email}")
            print(f"[DEBUG] Full context_params: {context_params}")
                    
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
            
            # if step == "name":
            #     name = user_query.strip()
            #     print(f"[Contact via Fallback] Name: {name}")
                
            #     return JsonResponse({
            #         "fulfillmentText": f"Thanks {name}! 😊\n\nAapka phone number kya hai?",
            #         "outputContexts": [
            #             {
            #                 "name": f"{session}/contexts/collect-details",
            #                 "lifespanCount": 10,
            #                 "parameters": {
            #                     "service": service,
            #                     "answers": answers,
            #                     "name": name,
            #                     "step": "phone"
            #                 }
            #             }
            #         ]
            #     })
            
            # elif step == "phone":
            #     phone = user_query.strip()
            #     print(f"[Contact via Fallback] Phone: {phone}")
                
            #     return JsonResponse({
            #         "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
            #         "outputContexts": [
            #             {
            #                 "name": f"{session}/contexts/collect-details",
            #                 "lifespanCount": 10,
            #                 "parameters": {
            #                     "service": service,
            #                     "answers": answers,
            #                     "name": context_params.get("name"),
            #                     "phone": phone,
            #                     "step": "email"
            #                 }
            #             }
            #         ]
            #     })
            
            if step == "name":
                # Get name from user query directly
                name = user_query.strip()
                
                # Validate
                if len(name) < 2:
                    return JsonResponse({
                        "fulfillmentText": "⚠️ Please enter a valid name (at least 2 characters)."
                    })
                
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
                                "name": name,  # ✅ SAVE HERE
                                "step": "phone"
                            }
                        }
                    ]
                })

            elif step == "phone":
                # Get phone from user query directly
                phone = user_query.strip()
                
                # Validate
                if len(phone) < 10:
                    return JsonResponse({
                        "fulfillmentText": "⚠️ Please enter a valid phone number (at least 10 digits)."
                    })
                
                print(f"[Contact via Fallback] Phone: {phone}")
                
                # ✅ GET NAME FROM CONTEXT
                saved_name = context_params.get("name", "Guest User")
                
                return JsonResponse({
                    "fulfillmentText": "Great! 📱\n\nAur aapka email address?",
                    "outputContexts": [
                        {
                            "name": f"{session}/contexts/collect-details",
                            "lifespanCount": 10,
                            "parameters": {
                                "service": service,
                                "answers": answers,
                                "name": saved_name,  # ✅ PRESERVE NAME
                                "phone": phone,      # ✅ SAVE PHONE
                                "step": "email"
                            }
                        }
                    ]
                })
            
            elif step == "email":
                email = user_query.strip()
    
                print(f"[Contact] Email collected: {email}")
                
                # ✅ MAIN FIX: Extract name/phone from PREVIOUS context responses
                # Don't rely on current parameters - they're empty!
                
                # Get from context (saved from previous steps)
                context_name = context_params.get("name", "")
                context_phone = context_params.get("phone", "")
                
                # Also check parameters (backup)
                param_name = parameters.get("name")
                param_phone = parameters.get("phone")
                
                # Extract from dict if needed
                if isinstance(param_name, dict):
                    param_name = param_name.get("name", "")
                if isinstance(param_phone, dict):
                    param_phone = param_phone.get("phone", "")
                
                # Priority: Use context values (from previous steps)
                lead_name = context_name if context_name and context_name.strip() else param_name
                lead_phone = context_phone if context_phone and context_phone.strip() else param_phone
                
                # Final fallback
                if not lead_name or lead_name.strip() == '':
                    lead_name = "Guest User"
                if not lead_phone or lead_phone.strip() == '':
                    lead_phone = "Not provided"

                print(f"[Contact] ✅ Name: {lead_name}")
                print(f"[Contact] ✅ Phone: {lead_phone}")
                print(f"[Contact] ✅ Email: {email}")
                print(f"[DEBUG] Context name: '{context_name}'")
                print(f"[DEBUG] Context phone: '{context_phone}'")
                print(f"[DEBUG] Param name: '{param_name}'")
                print(f"[DEBUG] Param phone: '{param_phone}'")

                # email = user_query.strip()
                # print(f"[Contact via Fallback] Email: {email}")

                # lead_name = context_params.get("name", "Not provided")
                # lead_phone = context_params.get("phone", "Not provided")

                # print(f"[Lead Data via Fallback] Name: {lead_name}")
                # print(f"[Lead Data via Fallback] Phone: {lead_phone}")
                # print(f"[Lead Data via Fallback] Email: {email}")

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