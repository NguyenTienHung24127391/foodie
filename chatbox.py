import json
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import re
from typing import List, Dict, Any
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS



# ================================
# 🔑 CHỖ ĐỂ ĐỔI KEY GEMINI (CHỈ THAY Ở ĐÂY)
# ================================
GEMINI_API_KEY = "AIzaSyAD5iadP1y6VfM89kqeN1BuMFsn1posqXc"  # <- đổi key ở đây
GEMINI_MODEL_NAME = "models/gemini-2.5-flash"      # có thể đổi model nếu cần

# Cấu hình gemini
genai.configure(api_key=GEMINI_API_KEY)

# ================================
# ⚙️ 1. Khởi tạo (giữ nguyên)
# ================================
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
chroma_client = chromadb.Client(chromadb.config.Settings(persist_directory="./chroma_db")) #lưu trữ local
collection = chroma_client.get_or_create_collection("restaurants")

# ================================
# 📂 2. Nạp dữ liệu JSON (ĐÃ SỬA LỖI METADATA)
# ================================
count = len(collection.get()["ids"])
if count == 0:
    print("🆕 Database trống — bắt đầu nạp dữ liệu JSON...")

    with open("foods.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    docs, metas, ids = [], [], []
    for i, item in enumerate(data):
        text = f"""
        Tên món: {item['name']}
        Xuất xứ: {item['origin']}
        Loại: {item['category']}
        Giá: {item['price_range']}
        Độ phổ biến: {item['popularity_score']}
        Nguyên liệu: {', '.join(item['ingredients'])}
        Lịch sử: {item['history']}
        Hương vị: {item['taste']}
        Gợi ý: {' | '.join(item['suggestions'])}
        """
        docs.append(text)
        metas.append({
            "name": item["name"],
            "origin": item["origin"],
            "category": item["category"],
            "price_range": item["price_range"],
            "taste": item["taste"],
            "popularity_score": item["popularity_score"],
            "ingredients": ', '.join(item["ingredients"]),
            "suggestions": ' | '.join(item["suggestions"])
        })
        ids.append(str(i))

    embeddings = model.encode(docs).tolist()
    collection.add(documents=docs, embeddings=embeddings, ids=ids, metadatas=metas)
    # chroma_client.persist()
    print(f"✅ Đã nạp {len(docs)} món ăn vào database.")
else:
    print(f"✅ Database đã có sẵn {count} mục, không cần nạp lại.")

# ================================
# 🧠 3. Hệ thống AI nâng cao (giữ nguyên logic)
# ================================
class AdvancedConversationManager:
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {
            "liked_dishes": [],
            "disliked_dishes": [],
            "price_preference": None,
            "taste_preference": None,
            "location_interest": None
        }
        
        # Từ khóa ẩm thực mở rộng và thông minh hơn
        self.food_keywords = self._build_food_keywords()
        
    def _build_food_keywords(self):
        base_keywords = [
            'món', 'ăn', 'đồ ăn', 'thức ăn', 'nhà hàng', 'quán', 'tiệm', 
            'food', 'restaurant', 'cafe', 'cà phê', 'bún', 'phở', 'cơm',
            'cháo', 'lẩu', 'nướng', 'hải sản', 'chay', 'vịt', 'gà', 'bò',
            'heo', 'tôm', 'cá', 'rau', 'canh', 'lòng', 'tiết canh', 'nem',
            'chả', 'giò', 'bánh', 'tráng miệng', 'trà', 'sinh tố', 'nước ép',
            'đồ uống', 'cocktail', 'bia', 'rượu', 'ngon', 'dở', 'đắng', 'cay',
            'ngọt', 'mặn', 'chua', 'béo', 'thơm', 'giòn', 'dai', 'mềm'
        ]
        
        # Thêm tất cả tên món từ database
        for item in data:
            base_keywords.extend(item['name'].lower().split())
            base_keywords.extend(item['category'].lower().split())
            base_keywords.extend([ing.lower() for ing in item['ingredients']])
        
        return list(set(base_keywords))
    
    def analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """Phân tích ý định câu hỏi một cách thông minh"""
        question_lower = question.lower()
        
        intent = {
            "type": "general",
            "is_food_related": False,
            "specific_dish": None,
            "location": None,
            "price_range": None,
            "taste": None,
            "comparison": False,
            "recommendation": False
        }
        
        # Kiểm tra liên quan đến ẩm thực
        for keyword in self.food_keywords:
            if keyword in question_lower:
                intent["is_food_related"] = True
                break
        
        # Phân tích ý định chi tiết
        if any(word in question_lower for word in ['gì', 'gì không', 'recommend', 'đề xuất', 'nên', 'nào ngon']):
            intent["recommendation"] = True
            intent["type"] = "recommendation"
        
        if any(word in question_lower for word in ['ở đâu', 'địa chỉ', 'quán', 'nhà hàng', 'chỗ nào']):
            intent["type"] = "location"
        
        if any(word in question_lower for word in ['giá', 'đắt', 'rẻ', 'bao nhiêu', 'mắc']):
            intent["type"] = "price"
            if 'rẻ' in question_lower or 'ít tiền' in question_lower:
                intent["price_range"] = "low"
            elif 'mắc' in question_lower or 'đắt' in question_lower:
                intent["price_range"] = "high"
        
        if any(word in question_lower for word in ['vị', 'ngon', 'dở', 'cay', 'ngọt', 'mặn', 'chua']):
            intent["type"] = "taste"
            if 'cay' in question_lower:
                intent["taste"] = "cay"
            elif 'ngọt' in question_lower:
                intent["taste"] = "ngọt"
        
        if any(word in question_lower for word in ['so sánh', 'hơn', 'khác']):
            intent["comparison"] = True
        
        # Phát hiện tên món cụ thể
        for item in data:
            if item['name'].lower() in question_lower:
                intent["specific_dish"] = item['name']
                break
        
        # Phát hiện địa điểm
        locations = ['hà nội', 'hồ chí minh', 'sài gòn', 'đà nẵng', 'huế', 'hội an']
        for loc in locations:
            if loc in question_lower:
                intent["location"] = loc
                break
        
        return intent
    
    def update_user_preferences(self, question: str, response: str):
        """Cập nhật sở thích người dùng từ hội thoại"""
        question_lower = question.lower()
        
        # Cập nhật sở thích giá
        if 'rẻ' in question_lower:
            self.user_preferences["price_preference"] = "low"
        elif 'mắc' in question_lower or 'đắt' in question_lower:
            self.user_preferences["price_preference"] = "high"
        
        # Cập nhật sở thích vị
        tastes = ['cay', 'ngọt', 'mặn', 'chua', 'béo']
        for taste in tastes:
            if taste in question_lower:
                self.user_preferences["taste_preference"] = taste
                break
        
        # Cập nhật món không thích
        if 'không thích' in question_lower or 'không ăn' in question_lower:
            for item in data:
                if item['name'].lower() in question_lower and item['name'] not in self.user_preferences["disliked_dishes"]:
                    self.user_preferences["disliked_dishes"].append(item['name'])
    
    def is_food_related(self, question: str) -> bool:
        """Kiểm tra thông minh hơn xem câu hỏi liên quan đến ẩm thực"""
        intent = self.analyze_question_intent(question)
        return intent["is_food_related"]
    
    def handle_general_conversation(self, question: str) -> str:
        """Xử lý hội thoại thông thường thông minh hơn"""
        question_lower = question.lower()
        
        general_responses = {
            'chào': "👋 Chào bạn! Mình là Deadline - chuyên gia ẩm thực Gen Z đây! Bạn muốn khám phá món gì ngon today? 😎",
            'bạn là ai': "🌟 Mình là Deadline - food expert siêu cấp vippro! Mình biết hết các món ngon từ truyền thống đến trend mới nhất. Hiện mình đang quản lý thông tin về 35+ món ăn đặc sắc!",
            'cảm ơn': "😊 Có gì đâu! Mình sống để recommend đồ ăn ngon mà. Còn gì muốn hỏi nữa không?",
            'tạm biệt': "👋 Bye bye! Nhớ ăn uống đầy đủ và thử món mới nhé! Hẹn gặp lại 🍕",
            'khỏe không': "💪 Mình khỏe lắm! Đang full năng lượng để recommend đồ ăn ngon đây. Có món gì bạn muốn khám phá không?",
            'làm gì': "🍳 Mình đang nghiên cứu các món ăn mới để recommend cho bạn nè!",
            'biết bao nhiêu': f"📊 Hiện tại mình đang quản lý thông tin chi tiết của {len(data)} món ăn đặc sắc từ khắp Việt Nam!",
            'món nào': "🍽️ Mình biết rất nhiều món từ Bắc vào Nam! Bạn thích ăn gì? Mình có thể gợi ý phù hợp với sở thích của bạn!",
            '?': "🤔 Bạn muốn hỏi gì về ẩm thực nào? Mình có thể giúp tìm món ngon, gợi ý quán ăn, hoặc tư vấn về nguyên liệu đó!"
        }
        
        for key, response in general_responses.items():
            if key in question_lower:
                return response
        
        # Phản hồi thông minh cho các câu hỏi không rõ ràng
        if len(question.strip()) < 3:
            return "🤔 Bạn có thể nói rõ hơn một chút được không? Mình muốn hiểu để giúp bạn tìm món ngon phù hợp nhất! 😊"
        
        return "🍕 Mình chuyên về ẩm thực, nhưng nếu bạn muốn tìm món gì ngon, gợi ý quán ăn, hay tư vấn về nguyên liệu, mình sẵn sàng help! Bạn thích ăn gì? 😋"

    def add_to_history(self, role: str, message: str):
        self.conversation_history.append({"role": role, "content": message})
        if len(self.conversation_history) > 8:
            self.conversation_history = self.conversation_history[-6:]

# Khởi tạo conversation manager
conv_manager = AdvancedConversationManager()

# ================================
# Hàm gọi Gemini để sinh câu trả lời (thêm)
# ================================
def generate_answer_with_gemini(prompt: str) -> str:
    """
    Gọi Gemini (google.generativeai). Nếu API mới đổi, hàm này có thể cần chỉnh model name.
    Thay key: sửa GEMINI_API_KEY ở đầu file.
    """
    try:
        # Cách gọi đơn giản: genai.generate_text (nếu phiên bản hỗ trợ)
        try:
            # Một số phiên bản trả về dict với 'candidates' hoặc 'content'
            resp = genai.generate_text(model=GEMINI_MODEL_NAME, prompt=prompt, temperature=0.8, max_output_tokens=600)
            # Try common field names:
            if isinstance(resp, dict):
                if 'candidates' in resp and len(resp['candidates']) > 0:
                    return resp['candidates'][0].get('content', '').strip()
                if 'content' in resp:
                    return resp['content'].strip()
            # If resp has .text
            text = getattr(resp, 'text', None)
            if text:
                return text.strip()
        except Exception:
            # Fallback to GenerativeModel API surface if available
            try:
                gm = genai.GenerativeModel(GEMINI_MODEL_NAME)
                r = gm.generate_content(prompt)
                # r may have 'text' or 'content' attribute
                return getattr(r, 'text', getattr(r, 'content', '')).strip()
            except Exception as e2:
                # raise outer to go to fallback
                raise e2
    except Exception as e:
        print("⚠️ Lỗi khi gọi Gemini:", e)
        raise

# ================================
# Các hàm xử lý (giữ nguyên phần còn lại của code)
# ================================
def _smart_filter_results(results, intent, user_preferences):
    """Lọc kết quả thông minh dựa trên ý định và sở thích"""
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    
    filtered_docs = []
    filtered_metas = []
    
    for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
        # Phân tích document
        doc_info = _parse_document_info(doc)
        
        # Loại bỏ món người dùng không thích
        if meta.get("name") in user_preferences["disliked_dishes"]:
            continue
            
        # Lọc theo ý định
        if intent["price_range"] == "low" and "40,000" not in doc_info.get("price", ""):
            continue
        if intent["price_range"] == "high" and "40,000" in doc_info.get("price", ""):
            continue
        if intent["taste"] and intent["taste"] not in doc_info.get("taste", "").lower():
            continue
        if intent["location"] and intent["location"] not in doc_info.get("origin", "").lower():
            continue
        
        filtered_docs.append(doc)
        filtered_metas.append(meta)
    
    return filtered_docs[:3], filtered_metas[:3]  # Giới hạn 3 kết quả tốt nhất

def _parse_document_info(doc: str) -> Dict[str, str]:
    """Phân tích thông tin từ document"""
    info = {}
    lines = [ln.strip() for ln in doc.splitlines() if ":" in ln]
    for ln in lines:
        try:
            k, v = ln.split(":", 1)
            info[k.strip()] = v.strip()
        except:
            continue
    return info

def _handle_no_results(question: str, intent: Dict) -> str:
    """Xử lý khi không có kết quả phù hợp"""
    question_lower = question.lower()
    
    if intent["price_range"] == "low":
        return "💰 Hiện mình chưa tìm thấy món nào có giá rẻ phù hợp. Bạn có thể thử các món phổ thông như cơm, phở, bún thông thường nhé!"
    elif intent["price_range"] == "high":
        return "💎 Mình chủ yếu tập trung vào các món ăn bình dân và đặc sản địa phương. Bạn có muốn thử các món đặc sản vùng miền không?"
    elif intent["taste"]:
        return f"🌶️ Mình có một số món có vị {intent['taste']} như hủ tiếu sa tế, lẩu Thái... Bạn muốn mình gợi ý cụ thể không?"
    else:
        return "🤔 Mình chưa tìm thấy món ăn phù hợp với yêu cầu của bạn. Bạn có thể:\n• Mô tả rõ hơn về món bạn muốn\n• Cho mình biết sở thích ăn uống của bạn\n• Hoặc để mình gợi ý một số món đặc sản nổi tiếng! 😊"

def _build_smart_prompt(question: str, intent: Dict, docs: List[str], metas: List[Dict], conv_manager: AdvancedConversationManager) -> str:
    """Xây dựng prompt thông minh"""
    
    retrieved_info = "\n\n".join([
        f"Món {i+1}:\n{doc}" for i, doc in enumerate(docs)
    ])
    
    user_context = ""
    if conv_manager.user_preferences["price_preference"]:
        user_context += f"Sở thích giá: {conv_manager.user_preferences['price_preference']}\n"
    if conv_manager.user_preferences["taste_preference"]:
        user_context += f"Sở thích vị: {conv_manager.user_preferences['taste_preference']}\n"
    if conv_manager.user_preferences["disliked_dishes"]:
        user_context += f"Món không thích: {', '.join(conv_manager.user_preferences['disliked_dishes'])}\n"
    
    prompt = f"""
Bạn là Deadline - chatbot ẩm thực Gen Z cực kỳ thông minh và am hiểu.

PHÂN TÍCH Ý ĐỊNH CÂU HỎI:
- Loại câu hỏi: {intent['type']}
- Món cụ thể: {intent['specific_dish'] or 'Không'}
- Địa điểm: {intent['location'] or 'Không'}
- Khoảng giá: {intent['price_range'] or 'Không'}
- Vị: {intent['taste'] or 'Không'}
- So sánh: {'Có' if intent['comparison'] else 'Không'}
- Đề xuất: {'Có' if intent['recommendation'] else 'Không'}

THÔNG TIN NGƯỜI DÙNG:
{user_context}

LỊCH SỬ HỘI THOẠI GẦN ĐÂY:
{str(conv_manager.conversation_history[-3:])}

THÔNG TIN TỪ DATABASE:
{retrieved_info}

CÂU HỎI: {question}

YÊU CẦU TRẢ LỜI:
1. PHẢI thông minh, hiểu ngữ cảnh và ý định thực sự của câu hỏi
2. Nếu là so sánh, hãy so sánh chi tiết các món
3. Nếu là đề xuất, chọn món PHÙ HỢP NHẤT với ý định
4. Nếu người dùng từ chối món trước, ĐỪNG đề xuất lại
5. Trả lời như một người bạn am hiểu ẩm thực
6. Tự nhiên, Gen Z, nhưng KHÔNG quá màu mè
7. Nếu không chắc chắn, hãy hỏi lại cho rõ

Hãy trả lời MỘT CÁCH THÔNG MINH NHẤT:
"""
    
    return prompt

def _advanced_fallback_reply(docs: List[str], metas: List[Dict], question: str, intent: Dict, conv_manager: AdvancedConversationManager) -> str:
    """Fallback cực kỳ thông minh"""
    
    if not docs:
        return _handle_no_results(question, intent)
    
    # Phân tích tất cả documents
    dishes_info = []
    for doc, meta in zip(docs, metas):
        info = _parse_document_info(doc)
        info.update(meta)  # Kết hợp với metadata
        dishes_info.append(info)
    
    # Xử lý theo ý định
    if intent["comparison"] and len(dishes_info) >= 2:
        return _generate_comparison_response(dishes_info, intent)
    elif intent["recommendation"]:
        return _generate_recommendation_response(dishes_info, intent, conv_manager.user_preferences)
    elif intent["specific_dish"]:
        return _generate_specific_dish_response(dishes_info[0], intent)
    else:
        return _generate_general_response(dishes_info, intent, question)

def _generate_comparison_response(dishes_info: List[Dict], intent: Dict) -> str:
    """Tạo phản hồi so sánh thông minh"""
    response = "🔍 So sánh chi tiết:\n\n"
    
    for i, dish in enumerate(dishes_info[:3], 1):
        response += f"🍽️ {dish.get('name', 'Món')}:\n"
        response += f"   • Xuất xứ: {dish.get('origin', 'N/A')}\n"
        response += f"   • Giá: {dish.get('price_range', 'N/A')}\n"
        response += f"   • Vị: {dish.get('taste', 'N/A')}\n"
        if i < len(dishes_info[:3]):
            response += "\n"
    
    # Kết luận thông minh
    if intent["price_range"] == "low":
        cheapest = min(dishes_info, key=lambda x: _extract_price(x.get('price_range', '')))
        response += f"\n💡 Nếu bạn muốn tiết kiệm: {cheapest.get('name')} là lựa chọn tốt nhất!"
    elif intent["price_range"] == "high":
        expensive = max(dishes_info, key=lambda x: _extract_price(x.get('price_range', '')))
        response += f"\n💎 Nếu muốn trải nghiệm cao cấp: {expensive.get('name')} là lựa chọn đáng giá!"
    
    return response

def _extract_price(price_str: str) -> int:
    """Trích xuất giá trị giá từ chuỗi"""
    numbers = re.findall(r'\d+', price_str)
    return int(numbers[0]) if numbers else 0

def _generate_recommendation_response(dishes_info: List[Dict], intent: Dict, preferences: Dict) -> str:
    """Tạo phản hồi đề xuất thông minh"""
    # Lọc theo sở thích
    filtered_dishes = dishes_info
    if preferences["price_preference"] == "low":
        filtered_dishes = sorted(filtered_dishes, key=lambda x: _extract_price(x.get('price_range', '')))
    elif preferences["price_preference"] == "high":
        filtered_dishes = sorted(filtered_dishes, key=lambda x: _extract_price(x.get('price_range', '')), reverse=True)
    
    if preferences["taste_preference"]:
        filtered_dishes = [d for d in filtered_dishes if preferences["taste_preference"] in d.get('taste', '').lower()]
    
    # Loại bỏ món không thích
    filtered_dishes = [d for d in filtered_dishes if d.get('name') not in preferences["disliked_dishes"]]
    
    if not filtered_dishes:
        filtered_dishes = dishes_info
    
    best_dish = filtered_dishes[0]
    
    response = f"🌟 MÌNH ĐỀ XUẤT: {best_dish.get('name')}\n\n"
    response += f"📍 Xuất xứ: {best_dish.get('origin')}\n"
    response += f"🎯 Vị: {best_dish.get('taste')}\n"
    response += f"💵 Giá: {best_dish.get('price_range', 'N/A')}\n"
    
    # Lý do đề xuất
    reasons = []
    if preferences["price_preference"]:
        reasons.append("phù hợp ngân sách")
    if preferences["taste_preference"]:
        reasons.append("đúng vị bạn thích")
    if intent["location"]:
        reasons.append("đặc sản địa phương")
    
    if reasons:
        response += f"💡 Lý do: {', '.join(reasons)}\n"
    
    # Alternative (tránh món không thích)
    alternatives = [d for d in filtered_dishes[1:] if d.get('name') not in preferences["disliked_dishes"]]
    if alternatives:
        response += f"\n⚡ Alternative: {alternatives[0].get('name')} cũng rất đáng thử!"
    
    return response

def _generate_specific_dish_response(dish_info: Dict, intent: Dict) -> str:
    """Tạo phản hồi cho món cụ thể"""
    response = f"🍳 {dish_info.get('name')} - {dish_info.get('category')}\n"
    
    if dish_info.get('origin'):
        response += f"📍 Xuất xứ: {dish_info.get('origin')}\n"
    
    if intent["type"] == "taste":
        response += f"🎯 Vị đặc trưng: {dish_info.get('taste')}\n"
    elif intent["type"] == "price":
        response += f"💵 Giá: {dish_info.get('price_range', 'N/A')}\n"
    else:
        response += f"🎯 Vị: {dish_info.get('taste')}\n"
        response += f"💵 Giá: {dish_info.get('price_range', 'N/A')}\n"
    
    if dish_info.get('ingredients'):
        response += f"🍴 Nguyên liệu: {dish_info.get('ingredients')}\n"
    
    return response

def _generate_general_response(dishes_info: List[Dict], intent: Dict, question: str) -> str:
    """Tạo phản hồi chung thông minh"""
    main_dish = dishes_info[0]
    
    response = f"🍽️ {main_dish.get('name')} - {main_dish.get('category')}"
    if main_dish.get('origin'):
        response += f" từ {main_dish.get('origin')}"
    response += "\n\n"
    
    response += f"🎯 Đặc điểm: {main_dish.get('taste')}\n"
    response += f"💵 Giá: {main_dish.get('price_range', 'N/A')}\n"
    
    if len(dishes_info) > 1:
        other_dishes = [d.get('name') for d in dishes_info[1:3] if d.get('name')]
        if other_dishes:
            response += f"\n🔍 Món liên quan: {', '.join(other_dishes)}"
    
    response += f"\n\n❓ Bạn muốn biết thêm chi tiết gì về {main_dish.get('name')} không?"
    
    return response

# ================================
# 🚀 4. Chạy thử - dùng Gemini để trả lời tự nhiên
# ================================
# def smart_rag_chat(question: str):
#     """Phiên bản RAG thông minh hơn với phân tích ngữ cảnh"""
    
#     # Thêm câu hỏi vào lịch sử
#     conv_manager.add_to_history("user", question)
    
#     # Phân tích ý định câu hỏi
#     intent = conv_manager.analyze_question_intent(question)
    
#     # Xử lý câu hỏi không liên quan đến ẩm thực
#     if not intent["is_food_related"]:
#         response = conv_manager.handle_general_conversation(question)
#         conv_manager.add_to_history("assistant", response)
#         print(response)
#         return
    
#     # Tìm kiếm thông minh dựa trên ý định
#     query_emb = model.encode([question]).tolist()[0]
    
#     # Điều chỉnh số lượng kết quả dựa trên loại câu hỏi
#     n_results = 5 if intent["comparison"] or intent["recommendation"] else 3
    
#     results = collection.query(
#         query_embeddings=[query_emb], 
#         n_results=n_results,
#         include=["documents", "metadatas", "distances"]
#     )
    
#     # Lọc kết quả thông minh hơn
#     filtered_docs, filtered_metas = _smart_filter_results(
#         results, intent, conv_manager.user_preferences
#     )
    
#     if not filtered_docs:
#         response = _handle_no_results(question, intent)
#         conv_manager.add_to_history("assistant", response)
#         print(response)
#         return
    
#     # Cập nhật sở thích người dùng
#     conv_manager.update_user_preferences(question, "")
    
#     # Tạo prompt thông minh hơn (giữ nguyên)
#     prompt = _build_smart_prompt(question, intent, filtered_docs, filtered_metas, conv_manager)
    
#     try:
#         # Gọi Gemini để tạo câu trả lời tự nhiên
#         try:
#             content = generate_answer_with_gemini(prompt)
#         except Exception as e:
#             # nếu gọi Gemini lỗi -> dùng fallback cục bộ (không crash)
#             print("⚠️ Gemini lỗi, dùng fallback:", e)
#             content = _advanced_fallback_reply(filtered_docs, filtered_metas, question, intent, conv_manager)
        
#     except Exception as e:
#         # Fallback thông minh hơn (nếu có lỗi khác)
#         content = _advanced_fallback_reply(filtered_docs, filtered_metas, question, intent, conv_manager)
    
#     # Thêm phản hồi vào lịch sử và in ra
#     conv_manager.add_to_history("assistant", content)
#     print(content)

def smart_rag_chat(question: str) -> str:
    """Phiên bản RAG thông minh hơn với phân tích ngữ cảnh"""
    
    conv_manager.add_to_history("user", question)
    
    intent = conv_manager.analyze_question_intent(question)
    
    if not intent["is_food_related"]:
        response = conv_manager.handle_general_conversation(question)
        conv_manager.add_to_history("assistant", response)
        print(response)
        return str(response)  # ✅ return string
    
    query_emb = model.encode([question]).tolist()[0]
    n_results = 5 if intent["comparison"] or intent["recommendation"] else 3
    
    results = collection.query(
        query_embeddings=[query_emb], 
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    
    filtered_docs, filtered_metas = _smart_filter_results(
        results, intent, conv_manager.user_preferences
    )
    
    if not filtered_docs:
        response = _handle_no_results(question, intent)
        conv_manager.add_to_history("assistant", response)
        print(response)
        return str(response)  # ✅ return string
    
    conv_manager.update_user_preferences(question, "")
    
    prompt = _build_smart_prompt(question, intent, filtered_docs, filtered_metas, conv_manager)
    
    try:
        try:
            content = generate_answer_with_gemini(prompt)
        except Exception as e:
            print("⚠️ Gemini lỗi, dùng fallback:", e)
            content = _advanced_fallback_reply(filtered_docs, filtered_metas, question, intent, conv_manager)
        
    except Exception as e:
        content = _advanced_fallback_reply(filtered_docs, filtered_metas, question, intent, conv_manager)
    
    conv_manager.add_to_history("assistant", content)
    print(content)
    return str(content)  # ✅ return string


# if __name__ == "__main__":
#     print("""
#     🍕 CHÀO MỪNG ĐẾN VỚI DEADLINE 2.0 - FOOD EXPERT SIÊU THÔNG MINH! 🍜
    
#     🤖 Mình có thể:
#     • HIỂU Ý ĐỊNH của câu hỏi
#     • SO SÁNH thông minh giữa các món
#     • GHI NHỚ sở thích của bạn
#     • ĐỀ XUẤT cực kỳ phù hợp
#     • XỬ LÝ ngữ cảnh phức tạp
    
#     Type 'exit' để thoát 😊
#     """)
    
#     while True:
#         try:
#             question = input("\n🧐 Bạn muốn hỏi gì: ").strip()
#             if question.lower() in ["quit", "exit", "bye"]:
#                 print("👋 Hẹn gặp lại! Nhớ ăn uống ngon miệng nha! 🍴")
#                 break
#             if question:
#                 smart_rag_chat(question)
#         except KeyboardInterrupt:
#             print("\n👋 Tạm biệt! Hẹn gặp lại!")
#             break
#         except Exception as e:
#             print(f"❌ Có lỗi xảy ra: {e}. Vui lòng thử lại!")
#             break

app = Flask(__name__)
CORS(app)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    print("Received from web:", data)  # Kiểm tra web gửi gì
    question = data.get("question", "").strip()
    # if not question:
    #     return jsonify({"answer": "❗ Vui lòng nhập câu hỏi hợp lệ."})
    
    answer = smart_rag_chat(question)
    # return jsonify({"answer": answer})
    if not isinstance(answer, str):
        print("Warning: smart_rag_chat không trả về string, dùng placeholder")
        answer = "Xin lỗi, mình chưa trả lời được câu hỏi này 😢"

    print("Answer length:", len(answer))

    print("Answer length:", len(answer))        # Chiều dài câu trả lời
    print("Answer preview:", answer[:100]) 
    return app.response_class(
        response=json.dumps({"answer": answer}, ensure_ascii=False),
        status=200,
        mimetype='application/json'
    )

# if __name__ == "__main__":
#     print("""
#     🍕 CHÀO MỪNG ĐẾN VỚI DEADLINE 2.0 - FOOD EXPERT SIÊU THÔNG MINH! 🍜

#     ⚙️ Flask server đang chạy tại: http://127.0.0.1:5000
#     Dùng endpoint: POST /ask để trò chuyện từ web chatbox.
#     """)
#     app.run(debug=True)
