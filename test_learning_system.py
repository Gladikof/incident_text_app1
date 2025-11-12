"""
Тестовий скрипт для перевірки системи навчання на історичних даних
"""
from app.database import SessionLocal
from app.services.learning_service import learning_service
from app.models import User
from app.core.enums import RoleEnum

def test_learning_system():
    db = SessionLocal()
    try:
        print("=" * 80)
        print("ТЕСТ СИСТЕМИ НАВЧАННЯ НА ІСТОРИЧНИХ ДАНИХ")
        print("=" * 80)

        # 1. Будуємо профілі експертизи на основі вирішених тікетів
        print("\n[1] Побудова профілів експертизи всіх спеціалістів...\n")
        expertise_profiles = learning_service.build_expertise_profiles(db)

        if not expertise_profiles:
            print("[!] Поки що немає вирішених тікетів для аналізу.")
            print("[INFO] Створіть кілька тікетів, призначте їх спеціалістам, та змініть статус на RESOLVED/CLOSED")
            print("[INFO] Після цього система автоматично навчиться на основі цих даних.\n")
        else:
            print(f"[OK] Знайдено профілі експертизи для {len(expertise_profiles)} спеціалістів:\n")
            for agent_id, keywords in expertise_profiles.items():
                agent = db.query(User).filter(User.id == agent_id).first()
                if agent:
                    top_5 = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:5]
                    print(f"  • {agent.full_name} ({agent.email})")
                    print(f"    Топ-5 ключових слів: {', '.join([f'{kw}({cnt})' for kw, cnt in top_5])}")

        # 2. Тестуємо підбір спеціаліста для різних типів тікетів
        print("\n" + "=" * 80)
        print("[2] Тестування підбору спеціаліста для різних тікетів...")
        print("=" * 80 + "\n")

        test_tickets = [
            {
                "text": "VPN connection not working. Cisco AnyConnect keeps disconnecting. Need help with remote access.",
                "description": "Тікет про VPN - має знайти Tom VPN Network"
            },
            {
                "text": "Local network switch problem. VLAN configuration issue. Ethernet cable not detected.",
                "description": "Тікет про локальну мережу - має знайти Sarah LAN Network"
            },
            {
                "text": "WiFi signal very weak. Access point not responding. Need wireless network troubleshooting.",
                "description": "Тікет про WiFi - має знайти Peter WiFi Network"
            },
            {
                "text": "Desktop computer won't boot. RAM memory error. Hard drive failure. Need hardware repair.",
                "description": "Тікет про desktop hardware - має знайти John Desktop Hardware"
            },
            {
                "text": "Laptop screen is broken. Battery not charging. Keyboard keys stuck.",
                "description": "Тікет про laptop hardware - має знайти Alice Laptop Hardware"
            },
            {
                "text": "Printer not working. Scanner driver issue. Monitor display problem.",
                "description": "Тікет про периферію - має знайти Mike Peripheral Hardware"
            },
            {
                "text": "Windows update failed. Microsoft Office Excel crash. Outlook email problem.",
                "description": "Тікет про Windows софт - має знайти Bob Windows Software"
            },
            {
                "text": "Need to install 1C application. SAP system access. Database SQL query error.",
                "description": "Тікет про бізнес-додатки - має знайти Maria Application Software"
            },
            {
                "text": "Software license expired. Activation key not working. Need antivirus subscription renewal.",
                "description": "Тікет про ліцензії - має знайти Anna License Software"
            },
            {
                "text": "Password reset needed. Account locked. Cannot login to system. Forgot credentials.",
                "description": "Тікет про паролі - має знайти David Password Access"
            },
        ]

        from app.core.enums import CategoryEnum

        # Знаходимо IT Support департамент
        it_dept = db.query(User).filter(
            User.role == RoleEnum.AGENT,
            User.email.contains("hardware")
        ).first()

        if not it_dept:
            print("[ERROR] IT Support департамент не знайдено")
            return

        department_id = it_dept.department_id

        for i, ticket_data in enumerate(test_tickets, 1):
            print(f"Тест {i}: {ticket_data['description']}")
            print(f"  Текст: {ticket_data['text'][:80]}...")

            recommended = learning_service.match_ticket_to_specialist_by_expertise(
                ticket_text=ticket_data['text'],
                category=CategoryEnum.HARDWARE,  # Категорія поки не важлива
                department_id=department_id,
                db=db
            )

            if recommended:
                print(f"  ✓ Рекомендовано: {recommended.full_name}")
                if recommended.specialty:
                    print(f"    Спеціалізація: {recommended.specialty}")
            else:
                print("  ✗ Не знайдено відповідного спеціаліста")
                print("    (Можливо немає історії вирішених тікетів)")

            print()

        # 3. Статистика спеціалістів
        print("=" * 80)
        print("[3] Статистика спеціалістів")
        print("=" * 80 + "\n")

        agents = db.query(User).filter(
            User.role == RoleEnum.AGENT,
            User.department_id == department_id
        ).all()

        for agent in agents[:5]:  # Перші 5 для прикладу
            stats = learning_service.get_specialist_stats(agent.id, db)
            print(f"• {agent.full_name} ({agent.email})")
            print(f"  Вирішено тікетів: {stats['total_resolved']}")
            if stats['by_category']:
                print(f"  По категоріях: {stats['by_category']}")
            if stats['top_keywords']:
                top_3 = stats['top_keywords'][:3]
                keywords_str = ', '.join([f"{kw['keyword']}({kw['count']})" for kw in top_3])
                print(f"  Топ-3 експертизи: {keywords_str}")
            print()

        print("=" * 80)
        print("[INFO] Система навчання готова до роботи!")
        print("[INFO] При створенні нових тікетів система автоматично:")
        print("  1. Аналізує ключові слова з тікету")
        print("  2. Порівнює з профілями експертизи спеціалістів")
        print("  3. Враховує поточне навантаження (активні тікети)")
        print("  4. Призначає найбільш досвідченого та доступного спеціаліста")
        print("=" * 80)

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_learning_system()
