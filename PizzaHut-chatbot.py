import json
from difflib import get_close_matches
from datetime import datetime, timedelta
import random


class PizzaHutChatbot:
    def __init__(self, data_file="pizza_data.json"):
        self.data_file = data_file
        self.data = self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as file:
                return json.load(file)
        except FileNotFoundError:
            print("Creating new data file...")
            return self.create_default_data()

    def save_data(self):
        with open(self.data_file, 'w', encoding='utf-8') as file:
            json.dump(self.data, file, indent=2, ensure_ascii=False)

    def create_default_data(self):
        # Create minimal default data structure
        default_data = {
            "restaurant_info": {
                "name": "Pizza Hut",
                "phone": "(123) 456-7890",
                "hours": {"monday": "11:00 AM - 11:00 PM"}
            },
            "menu": {"pizzas": [], "sides": [], "drinks": []},
            "delivery_zones": [],
            "promotions": [],
            "orders": [],
            "questions": [],
            "customer_feedback": [],
            "analytics": {"popular_items": [], "peak_hours": [], "busiest_days": []},
            "staff_notes": []
        }
        self.save_data()
        return default_data

    def get_menu_by_category(self, category):
        """显示特定类别的菜单"""
        if category not in self.data["menu"]:
            return "Sorry, that category doesn't exist."

        items = self.data["menu"][category]
        if not items:
            return f"No {category} available at the moment."

        result = f"🍕 {category.upper()}:\n"
        for item in items:
            if category == "pizzas":
                prices = f"RM{item['prices']['regular']}/RM{item['prices']['large']}/RM{item['prices']['family']}"
                result += f"• {item['name']} - {prices} (R/L/F)\n  {item['description']}\n"
            else:
                result += f"• {item['name']} - RM{item['price']}\n  {item['description']}\n"
        return result

    def check_delivery_area(self, area):
        """检查配送区域信息"""
        for zone in self.data["delivery_zones"]:
            if area.lower() in zone["area"].lower():
                fee_text = "FREE" if zone["delivery_fee"] == 0 else f"RM{zone['delivery_fee']}"
                return f"📍 {zone['area']}: Delivery {fee_text} (Min order: RM{zone['min_order']}, Time: {zone['estimated_time']})"
        return "Please call us to check if we deliver to your area: " + self.data["restaurant_info"]["phone"]

    def get_active_promotions(self):
        """获取当前活跃的促销信息"""
        active_promos = [p for p in self.data["promotions"] if p.get("is_active", False)]
        if not active_promos:
            return "No active promotions at the moment."

        result = "🎉 CURRENT DEALS:\n"
        for promo in active_promos:
            result += f"• {promo['title']}: {promo['description']}\n"
        return result

    def add_customer_order(self, customer_info, items):
        """添加新订单到系统"""
        order_id = f"ORD{len(self.data['orders']) + 1:03d}"
        new_order = {
            "order_id": order_id,
            "customer_name": customer_info.get("name", ""),
            "phone": customer_info.get("phone", ""),
            "address": customer_info.get("address", ""),
            "items": items,
            "subtotal": sum(item["total"] for item in items),
            "delivery_fee": 0,  # Calculate based on area
            "status": "received",
            "order_time": datetime.now().isoformat(),
            "estimated_delivery": (datetime.now() + timedelta(minutes=40)).isoformat()
        }

        self.data["orders"].append(new_order)
        self.save_data()
        return order_id

    def get_popular_items(self):
        """获取热门商品"""
        if not self.data["analytics"]["popular_items"]:
            return "Our most popular items are Pepperoni and Margherita pizzas!"

        result = "🔥 POPULAR ITEMS:\n"
        for item in self.data["analytics"]["popular_items"][:3]:
            # Find item name by ID
            item_name = "Unknown Item"
            for pizza in self.data["menu"]["pizzas"]:
                if pizza["id"] == item["item_id"]:
                    item_name = pizza["name"]
                    break
            result += f"• {item_name} ({item['order_count']} orders)\n"
        return result

    def add_feedback(self, order_id, rating, comment):
        """添加客户反馈"""
        feedback = {
            "order_id": order_id,
            "rating": rating,
            "comment": comment,
            "feedback_date": datetime.now().isoformat()
        }
        self.data["customer_feedback"].append(feedback)
        self.save_data()
        return "Thank you for your feedback!"

    def handle_query(self, user_input):
        """处理用户查询"""
        user_input_lower = user_input.lower()

        # Menu queries
        if "pizza" in user_input_lower and ("menu" in user_input_lower or "what" in user_input_lower):
            return self.get_menu_by_category("pizzas")

        if "side" in user_input_lower or "appetizer" in user_input_lower:
            return self.get_menu_by_category("sides")

        if "drink" in user_input_lower or "beverage" in user_input_lower:
            return self.get_menu_by_category("drinks")

        # Delivery queries
        if "deliver" in user_input_lower and any(
                area in user_input_lower for area in ["klcc", "pj", "subang", "petaling"]):
            for area in ["klcc", "pj", "subang", "petaling"]:
                if area in user_input_lower:
                    return self.check_delivery_area(area)

        # Promotion queries
        if any(word in user_input_lower for word in ["deal", "promotion", "discount", "offer"]):
            return self.get_active_promotions()

        # Popular items
        if "popular" in user_input_lower or "recommend" in user_input_lower:
            return self.get_popular_items()

        # Hours query
        if "hour" in user_input_lower or "open" in user_input_lower:
            hours = self.data["restaurant_info"]["hours"]
            return f"We're open: {hours.get('monday', 'Please call for hours')}"

        # Phone query
        if "phone" in user_input_lower or "call" in user_input_lower:
            return f"Call us at: {self.data['restaurant_info']['phone']}"

        # Check knowledge base
        questions = [q["question"] for q in self.data["questions"]]
        best_match = get_close_matches(user_input_lower, questions, n=1, cutoff=0.6)

        if best_match:
            for q in self.data["questions"]:
                if q["question"] == best_match[0]:
                    return q["answer"]

        return None

    def learn_new_response(self, question, answer):
        """学习新的问答对"""
        new_qa = {
            "question": question.lower(),
            "answer": answer,
            "category": "general",
            "added_date": datetime.now().isoformat()
        }
        self.data["questions"].append(new_qa)
        self.save_data()

    def run_chatbot(self):
        print("🍕 Welcome to Pizza Hut Delivery! 🍕")
        print("I can help you with:")
        print("• Menu and prices (try 'show pizza menu')")
        print("• Delivery areas (try 'deliver to KLCC')")
        print("• Current promotions (try 'any deals?')")
        print("• Popular recommendations")
        print("• Store hours and contact info")
        print("\nType 'quit' to exit or ask me anything!")
        print("-" * 50)

        while True:
            user_input = input("\n🍕 You: ").strip()

            if user_input.lower() == "quit":
                print("🍕 Bot: Thanks for choosing Pizza Hut! Have a great day! 🍕")
                break

            if not user_input:
                continue

            # Try to handle the query
            response = self.handle_query(user_input)

            if response:
                print(f"🍕 Bot: {response}")
            else:
                print("🍕 Bot: I don't have that information yet. Can you help me learn?")
                new_answer = input("📝 Please provide the answer, or type 'skip': ").strip()

                if new_answer.lower() != "skip" and new_answer:
                    self.learn_new_response(user_input, new_answer)
                    print("🍕 Bot: Thank you! I learned something new!")


# Run the chatbot
if __name__ == "__main__":
    chatbot = PizzaHutChatbot()
    chatbot.run_chatbot()