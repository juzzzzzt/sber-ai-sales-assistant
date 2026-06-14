import streamlit as st
from groq import Groq
from products_db import SYSTEM_PROMPT, EXAMPLE_QUERIES
import time

# Конфигурация страницы
st.set_page_config(
    page_title="SberCIB AI Sales Assistant",
    page_icon="CIB",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("AI Sales Assistant для ДГР")
st.caption("Прототип AI-ассистента для отдела электронных продаж Департамента Глобальных Рынков")
st.markdown("---")


# Инициализация Groq клиента (Llama 3.3 70B)
@st.cache_resource
def get_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


try:
    client = get_client()
except Exception as e:
    st.error(f"Ошибка подключения к Groq API: {e}")
    st.info("Добавьте GROQ_API_KEY в .streamlit/secrets.toml")
    st.stop()

# Инициализация истории сообщений
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Флаг для обработки примеров
if "process_example" not in st.session_state:
    st.session_state.process_example = False

# Боковая панель
with st.sidebar:
    st.header("О проекте")
    st.markdown("""
    **Pet-project для подготовки к интервью в Сбер КИБ**

    **Стек:**
    - Llama 3.3 70B (open-source)
    - Groq API (бесплатно)
    - Streamlit

    **Почему Llama?**
    Сбер использует open-source модели (ruGPT, SberGPT) для compliance.
    """)

    st.info("**Groq — самый быстрый LLM-инференс в мире!**")

    if st.button("Очистить диалог", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]
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

# Отображение истории диалога
for msg in st.session_state.messages[1:]:  # Пропускаем system prompt
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Обработка примеров из сайдбара
if st.session_state.process_example:
    # Получаем последнее сообщение пользователя
    last_message = st.session_state.messages[-1]

    if last_message["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Llama 3.3 анализирует запрос..."):
                start_time = time.time()
                try:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=st.session_state.messages,
                        temperature=0.7,
                        max_tokens=1500,
                    )
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

                    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

                except Exception as e:
                    assistant_msg = f"Ошибка при запросе к LLM: {str(e)}"
                    st.error(assistant_msg)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

        st.session_state.process_example = False
        st.rerun()

# Поле ввода пользователя
if prompt := st.chat_input("Задайте вопрос о продуктах ДГР..."):
    # Добавляем сообщение пользователя
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Запрос к Llama через Groq
    with st.chat_message("assistant"):
        with st.spinner("Llama 3.3 анализирует запрос..."):
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1500,
                )
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

            except Exception as e:
                assistant_msg = f"Ошибка при запросе к LLM: {str(e)}"
                st.error(assistant_msg)

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

# Footer
st.markdown("---")
st.caption("🎓 Pet-project для подготовки к интервью в Сбер КИБ | Чурилов Иван | 2026")