"""Benchmark script to test the AI Legal MVP against fixed questions."""

import asyncio

from app.agent import ask_question

QUESTIONS = [
    # Law questions (3)
    {
        "id": "law_1",
        "question": "Doanh nghiệp trên không gian mạng có trách nhiệm gì theo Luật An ninh mạng?",
        "expected_source": "24-2018-qh14",
        "category": "Luật An ninh mạng",
    },
    {
        "id": "law_2",
        "question": "Luật quy định thế nào về việc gỡ bỏ thông tin vi phạm trên không gian mạng?",
        "expected_source": "24-2018-qh14",
        "category": "Luật An ninh mạng",
    },
    {
        "id": "law_3",
        "question": "Những hành vi nào bị nghiêm cấm theo Luật An ninh mạng?",
        "expected_source": "24-2018-qh14",
        "category": "Luật An ninh mạng",
    },
    # Policy questions (2)
    {
        "id": "policy_1",
        "question": "Tôi nghi ngờ có sự cố an ninh thông tin thì phải làm gì?",
        "expected_source": "isms.md",
        "category": "Chính sách công ty",
    },
    {
        "id": "policy_2",
        "question": "Có mấy level bảo mật trong chính sách công ty?",
        "expected_source": "isms.md",
        "category": "Chính sách công ty",
    },
]


async def run_benchmark():
    print("=" * 80)
    print("AI LEGAL MVP - BENCHMARK RESULTS")
    print("=" * 80)
    print()

    for i, q in enumerate(QUESTIONS, 1):
        print(f"[{i}/{len(QUESTIONS)}] [{q['category']}]")
        print(f"Q: {q['question']}")
        print("-" * 60)

        try:
            answer = await asyncio.wait_for(
                ask_question(q["question"], f"benchmark_{q['id']}"),
                timeout=60,
            )
            print(f"A: {answer}")
        except asyncio.TimeoutError:
            print("A: TIMEOUT (exceeded 60 seconds)")
        except Exception as e:
            print(f"A: ERROR - {e}")

        print(f"\nExpected source: {q['expected_source']}")
        print("=" * 80)
        print()


if __name__ == "__main__":
    asyncio.run(run_benchmark())
