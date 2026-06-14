import streamlit as st
from groq import Groq
from products_db import SYSTEM_PROMPT, EXAMPLE_QUERIES, TOOLS, FUNCTION_MAP
import time
import json

# Конфигурация страницы
st.set_page_config(
    page_title="SberCIB AI Sales Assistant",
    page_icon="🏦",
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


# Функция для вызова LLM с поддержкой tool use
def call_llm_with_tools(messages, tools=None):
    """Вызов LLM с поддержкой tool use"""
    try:
        if tools:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1500,
            )
        else:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
            )
        return response
    except Exception as e:
        st.error(f"Ошибка при вызове LLM: {e}")
        return None


# Функция для обработки вызовов функций от LLM
def process_tool_calls(response, messages):
    """Обработка вызовов функций от LLM"""
    if not response:
        return "Ошибка при обработке запроса"

    message = response.choices[0].message

    # Если LLM хочет вызвать функцию
    if hasattr(message, 'tool_calls') and message.tool_calls:
        # Добавляем сообщение ассистента с вызовами
        messages_with_tools = messages + [{
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in message.tool_calls
            ]
        }]

        # Выполняем каждую функцию
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            try:
                function_args = json.loads(tool_call.function.arguments)
            except:
                function_args = {}

            # Показываем, что вызывается функция
            st.info(f"🔧 Вызов функции: {function_name}({function_args})")

            if function_name in FUNCTION_MAP:
                try:
                    function_response = FUNCTION_MAP[function_name](**function_args)

                    messages_with_tools.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": function_response
                    })
                except Exception as e:
                    error_msg = f"Ошибка выполнения функции: {str(e)}"
                    messages_with_tools.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_msg
                    })
            else:
                error_msg = f"Функция {function_name} не найдена"
                messages_with_tools.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": error_msg
                })

        # Повторный вызов LLM с результатами функций
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_with_tools,
            temperature=0.7,
            max_tokens=1500,
        )
        return final_response.choices[0].message.content

    return message.content if message.content else ""


# Боковая панель
with st.sidebar:
    st.header("О проекте")
    st.markdown("""
    **Pet-project для подготовки к интервью в Сбер КИБ**

    **Стек:**
    - Llama 3.3 70B (open-source)
    - Groq API (бесплатно)
    - Streamlit
    - Tool Use / Function Calling

    **Возможности:**
    - Получение рыночных котировок
    - Анализ портфеля клиента
    - Персональные рекомендации
    """)

    st.info("**GROQ + Tool Use**")

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
    last_message = st.session_state.messages[-1]

    if last_message["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Llama 3.3 анализирует запрос..."):
                start_time = time.time()
                try:
                    response = call_llm_with_tools(st.session_state.messages, tools=TOOLS)
                    assistant_msg = process_tool_calls(response, st.session_state.messages)
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
                        st.write(f"**🔧 Tool Use:** Активирован")

                    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

                except Exception as e:
                    assistant_msg = f"Ошибка при запросе к LLM: {str(e)}"
                    st.error(assistant_msg)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

        st.session_state.process_example = False
        st.rerun()

# Поле ввода пользователя
if prompt := st.chat_input("Задайте вопрос о продуктах ДГР..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Llama 3.3 анализирует запрос..."):
            start_time = time.time()
            try:
                response = call_llm_with_tools(st.session_state.messages, tools=TOOLS)
                assistant_msg = process_tool_calls(response, st.session_state.messages)
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
                    st.write(f"**🔧 Tool Use:** Активирован")

            except Exception as e:
                assistant_msg = f"Ошибка при запросе к LLM: {str(e)}"
                st.error(assistant_msg)

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

# Footer
st.markdown("---")
st.caption("Pet-project для подготовки к интервью в Сбер КИБ | Чурилов Иван | 2026")