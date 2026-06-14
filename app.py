import streamlit as st
from groq import Groq
from products_db import SYSTEM_PROMPT, EXAMPLE_QUERIES, MOCK_RATES, MOCK_CLIENT_PORTFOLIO, MOCK_NEWS
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

import plotly.express as px
import plotly.graph_objects as go

st.markdown("---")
st.header("📊 Анализ портфеля клиента (demo)")

if st.button("🔍 Проанализировать портфель ООО Ромашка"):
    portfolio = MOCK_CLIENT_PORTFOLIO["portfolio"]

    # Конвертация в рубли
    portfolio_rub = {
        "Облигации РФ": portfolio["RUB_bonds"]["amount"],
        "Акции РФ": portfolio["equities_RF"]["amount"],
        "USD (конверт.)": portfolio["USD_cash"]["amount"] * MOCK_RATES["USD_RUB"],
        "EUR (конверт.)": portfolio["EUR_cash"]["amount"] * MOCK_RATES["EUR_RUB"],
    }

    total_value = sum(portfolio_rub.values())

    # Расчёт валютной экспозиции (формула)
    fx_exposure = portfolio_rub["USD (конверт.)"] + portfolio_rub["EUR (конверт.)"]
    fx_exposure_pct = (fx_exposure / total_value) * 100

    # Расчёт дюрации портфеля (взвешенная средняя)
    weighted_duration = sum(
        (portfolio[k]["amount"] * (MOCK_RATES.get(f"{k.split('_')[0]}_RUB", 1) if k.endswith('_cash') else 1) *
         portfolio[k]["duration"])
        for k in portfolio.keys()
    )
    # Упрощённый расчёт: дюрация только для облигаций
    duration_numerator = portfolio["RUB_bonds"]["amount"] * portfolio["RUB_bonds"]["duration"]
    portfolio_duration = duration_numerator / total_value

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            values=list(portfolio_rub.values()),
            names=list(portfolio_rub.keys()),
            title="Распределение активов (в рублях)",
            hole=0.3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.metric("💰 Всего активов", f"{total_value / 1e6:.1f} млн ₽")
        st.metric("💱 Валютная экспозиция", f"{fx_exposure_pct:.1f}%")
        st.metric("⏱ Дюрация портфеля", f"{portfolio_duration:.2f} лет")

        # Формулы для прозрачности
        with st.expander("📐 Методология расчёта"):
            st.markdown(f"""
            **Валютная экспозиция:**
            ```
            (USD × курс + EUR × курс) / Общая стоимость портфеля
            = ({portfolio['USD_cash']['amount']:,} × {MOCK_RATES['USD_RUB']} + {portfolio['EUR_cash']['amount']:,} × {MOCK_RATES['EUR_RUB']}) / {total_value:,.0f}
            = {fx_exposure:,.0f} ₽ / {total_value:,.0f} ₽
            = {fx_exposure_pct:.1f}%
            ```

            **Дюрация портфеля (взвешенная средняя):**
            ```
            Σ(Вес актива × Дюрация актива)
            = ({portfolio['RUB_bonds']['amount']:,} × {portfolio['RUB_bonds']['duration']}) / {total_value:,.0f}
            = {portfolio_duration:.2f} лет
            ```

            *Дюрация для акций и cash принимается равной 0*
            """)

# ==========================================
# УЛУЧШЕНИЕ 3: Morning Briefing & Sentiment
# ==========================================
st.markdown("---")
st.header("AI Morning Briefing (Demo)")
st.caption("Автоматическая генерация брифинга для sales-трейдера на основе альтернативных данных и новостей")

if st.button("🚀 Сгенерировать утренний брифинг", use_container_width=True, type="primary"):

    # 1. Формируем блок новостей с эмодзи для наглядности
    sentiment_emojis = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}
    news_text = "\n".join([
        f"- [{n['time']}] {n['source']}: {n['headline']} {sentiment_emojis.get(n['sentiment'], '⚪')}"
        for n in MOCK_NEWS
    ])

    # 2. Формируем контекст с рыночными данными (чтобы LLM не галлюцинировала!)
    rates_text = f"Ключевая ставка ЦБ: {MOCK_RATES['key_rate_CB']}%, USD/RUB: {MOCK_RATES['USD_RUB']}, EUR/RUB: {MOCK_RATES['EUR_RUB']}"

    # 3. Создаем мощный промпт для LLM
    briefing_prompt = f"""Ты — старший аналитик Департамента Глобальных Рынков (ДГР) Сбера. 
Сгенерируй краткий и структурированный Morning Briefing для sales-трейдеров на основе следующих данных.

[РЫНОЧНЫЕ ДАННЫЕ]
{rates_text}

[НОВОСТНОЙ ПОТОК]
{news_text}

ТРЕБОВАНИЯ К ОТВЕТУ (строго в формате Markdown):
1. **Макро-обзор**: 2-3 предложения о главном драйвере дня.
2. **Влияние на продукты ДГР**: Как новости влияют на FX (валюту), Fixed Income (облигации) и Derivatives (деривативы).
3. **3 Идеи для клиентов**: Конкретные предложения, которые sales-трейдер может озвучить клиентам сегодня (например, хеджирование, размещение ликвидности).
4. **Риски дня**: На что обратить внимание.

Отвечай на русском языке, профессионально, без воды."""

    # 4. Вызываем LLM
    with st.spinner("AI-агент анализирует новости и рыночные данные..."):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system",
                     "content": "Ты профессиональный финансовый аналитик Сбера. Отвечай строго по данным из промпта."},
                    {"role": "user", "content": briefing_prompt}
                ],
                temperature=0.4,  # Низкая температура для более фактологического ответа
                max_tokens=1000,
            )

            # 5. Красивый вывод результата
            st.markdown(response.choices[0].message.content)

            # Метрики снизу
            col1, col2, col3 = st.columns(3)
            col1.metric("Проанализировано новостей", len(MOCK_NEWS))
            col2.metric("Позитивный фон",
                        f"{sum(1 for n in MOCK_NEWS if n['sentiment'] == 'positive')}/{len(MOCK_NEWS)}")
            col3.metric("Время генерации", f"{(response.usage.completion_tokens / 50):.1f} сек")  # Примерная оценка

        except Exception as e:
            st.error(f"Ошибка генерации брифинга: {e}")