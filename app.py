import streamlit as st
from groq import Groq
from products_db import SYSTEM_PROMPT, EXAMPLE_QUERIES, MOCK_RATES, MOCK_CLIENT_PORTFOLIO
import time
import json

st.set_page_config(
    page_title="SberCIB AI Sales Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("AI Sales Assistant для ДГР")
st.caption("Прототип AI-ассистента для отдела электронных продаж Департамента Глобальных Рынков")
st.markdown("---")


@st.cache_resource
def get_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


try:
    client = get_client()
except Exception as e:
    st.error(f"Ошибка подключения к Groq API: {e}")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

if "process_example" not in st.session_state:
    st.session_state.process_example = False


def get_contextual_data(user_message: str) -> str:
    """Извлекает данные на основе ключевых слов в сообщении"""
    message_lower = user_message.lower()

    # Проверяем, нужны ли курсы валют
    if any(word in message_lower for word in ['курс', 'доллар', 'евро', 'валюта', 'котировк', 'rate', 'usd', 'eur']):
        return f"\n\n[КОНТЕКСТ: Текущие рыночные данные]\n{json.dumps(MOCK_RATES, ensure_ascii=False, indent=2)}"

    # Проверяем, нужен ли портфель
    if any(word in message_lower for word in ['портфель', 'активы', 'позиции', 'portfolio', 'holding']):
        return f"\n\n[КОНТЕКСТ: Портфель клиента]\n{json.dumps(MOCK_CLIENT_PORTFOLIO, ensure_ascii=False, indent=2)}"

    return ""


def call_llm(messages, context=""):
    """Вызов LLM с контекстом"""
    try:
        # Добавляем контекст к последнему сообщению пользователя
        messages_with_context = messages.copy()
        if context and messages_with_context and messages_with_context[-1]["role"] == "user":
            messages_with_context[-1] = {
                "role": "user",
                "content": messages_with_context[-1]["content"] + context
            }

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_with_context,
            temperature=0.7,
            max_tokens=1500,
        )
        return response
    except Exception as e:
        st.error(f"Ошибка при вызове LLM: {e}")
        return None


# Sidebar
with st.sidebar:
    st.header("О проекте")
    st.markdown("""
    **Pet-project для подготовки к интервью в Сбер КИБ**

    **Стек:**
    - Llama 3.3 70B (open-source)
    - Groq API (бесплатно)
    - Streamlit

    **Возможности:**
    - Получение рыночных котировок
    - Анализ портфеля клиента
    - Персональные рекомендации
    """)

    if st.button("Очистить диалог", use_container_width=True):
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        st.rerun()

    st.markdown("---")
    st.header("Примеры запросов")
    for i, q in enumerate(EXAMPLE_QUERIES):
        if st.button(q, use_container_width=True, key=f"example_{i}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.session_state.process_example = True
            st.rerun()

    st.markdown("---")
    st.caption("Based on surveys by Dong et al. (2025), Fu (2025), Pippas et al. (2025)")

# Display history
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Process examples
if st.session_state.process_example:
    last_message = st.session_state.messages[-1]

    if last_message["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Llama 3.3 анализирует запрос..."):
                start_time = time.time()

                # Извлекаем контекст
                context = get_contextual_data(last_message["content"])
                if context:
                    st.info("📊 **Используются рыночные данные**")

                response = call_llm(st.session_state.messages, context)

                if response:
                    assistant_msg = response.choices[0].message.content
                    elapsed = time.time() - start_time

                    st.markdown(assistant_msg)

                    with st.expander("Статистика запроса"):
                        tokens = response.usage
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Prompt tokens", tokens.prompt_tokens)
                        col2.metric("Completion tokens", tokens.completion_tokens)
                        col3.metric("Total tokens", tokens.total_tokens)
                        st.write(f"**Время ответа:** {elapsed:.2f} сек")
                        st.write(f"**Модель:** Llama 3.3 70B (Groq)")
                        if context:
                            st.write(f"**📊 Контекст:** Добавлены рыночные данные")

                    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
                else:
                    st.error("Ошибка при обработке запроса")

        st.session_state.process_example = False
        st.rerun()

# User input
if prompt := st.chat_input("Задайте вопрос о продуктах ДГР..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Llama 3.3 анализирует запрос..."):
            start_time = time.time()

            # Извлекаем контекст
            context = get_contextual_data(prompt)
            if context:
                st.info("📊 **Используются рыночные данные**")

            response = call_llm(st.session_state.messages, context)

            if response:
                assistant_msg = response.choices[0].message.content
                elapsed = time.time() - start_time

                st.markdown(assistant_msg)

                with st.expander("Статистика запроса"):
                    tokens = response.usage
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Prompt tokens", tokens.prompt_tokens)
                    col2.metric("Completion tokens", tokens.completion_tokens)
                    col3.metric("Total tokens", tokens.total_tokens)
                    st.write(f"**Время ответа:** {elapsed:.2f} сек")
                    st.write(f"**Модель:** Llama 3.3 70B (Groq)")
                    if context:
                        st.write(f"**📊 Контекст:** Добавлены рыночные данные")

                st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
            else:
                st.error("Ошибка при обработке запроса")

st.markdown("---")
st.caption("Pet-project для подготовки к интервью в Сбер КИБ | Чурилов Иван | 2026")