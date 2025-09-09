import json
import os
from typing import Dict, List, Optional
from datetime import datetime

def generate_test_id(title: str, subject: str) -> str:
    """Генерирует уникальный ID для теста"""
    import re
    import time
    
    # Создаем ID на основе названия и предмета
    base_id = re.sub(r'[^a-zA-Z0-9]', '_', f"{subject}_{title}").lower()
    timestamp = str(int(time.time()))[-6:]  
    return f"{base_id}_{timestamp}"

def validate_test_data(test_data: Dict) -> tuple[bool, str]:
    """Валидирует данные теста"""
    required_fields = ["title", "subject", "test_type", "questions"]
    
    for field in required_fields:
        if field not in test_data:
            return False, f"Отсутствует обязательное поле: {field}"
    
    if test_data["test_type"] not in ["multiple_choice", "keyword_based"]:
        return False, "Неверный тип теста"
    
    if not isinstance(test_data["questions"], list) or len(test_data["questions"]) == 0:
        return False, "Тест должен содержать хотя бы один вопрос"
    
    # Валидация вопросов
    for i, question in enumerate(test_data["questions"]):
        if "question_text" not in question:
            return False, f"Вопрос {i+1}: отсутствует текст вопроса"
        
        if test_data["test_type"] == "multiple_choice":
            if "options" not in question or len(question["options"]) < 2:
                return False, f"Вопрос {i+1}: должно быть минимум 2 варианта ответа"
            if "correct_answer" not in question:
                return False, f"Вопрос {i+1}: не указан правильный ответ"
        elif test_data["test_type"] == "keyword_based":
            if "keywords" not in question or len(question["keywords"]) == 0:
                return False, f"Вопрос {i+1}: должны быть указаны ключевые слова"
            if "max_points" not in question or question["max_points"] <= 0:
                return False, f"Вопрос {i+1}: должно быть указано максимальное количество баллов"
    
    return True, "OK"

def convert_to_rubric_format(test_data: Dict) -> Dict:
    """Конвертирует тест в формат rubric.json для совместимости"""
    rubric = {
        "subject": test_data["subject"],
        "assignment_id": test_data["test_id"],
        "title": test_data["title"],
        "test_type": test_data["test_type"],  # Добавляем тип теста
        "questions": []
    }
    # Опциональный срок сдачи
    if test_data.get("due_date"):
        rubric["due_date"] = test_data["due_date"]
    if test_data.get("time_limit_minutes"):
        rubric["time_limit_minutes"] = int(test_data["time_limit_minutes"])
    
    for question in test_data["questions"]:
        if test_data["test_type"] == "keyword_based":
            # Для тестов с ключевыми словами - прямой перевод
            rubric["questions"].append({
                "question_id": question.get("question_id", f"q{len(rubric['questions'])+1}"),
                "title": question["question_text"],
                "max_points": question["max_points"],
                "keywords": question["keywords"]
            })
        elif test_data["test_type"] == "multiple_choice":
            # Для тестов с вариантами ответов - сохраняем все данные
            rubric["questions"].append({
                "question_id": question.get("question_id", f"q{len(rubric['questions'])+1}"),
                "title": question["question_text"],
                "max_points": question.get("max_points", 10),
                "options": question.get("options", []),
                "correct_answer": question.get("correct_answer", ""),
                "test_type": "multiple_choice"
            })
    
    return rubric