import hashlib
import io

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Кодирование ID плательщика", page_icon="🔒")

st.title("🔒 Кодирование ID плательщика")
st.caption(
    "Загрузите CSV-выгрузку. Приложение заменит «ID плательщика» на уникальный "
    "анонимный код (для каждого email — свой), а столбец «Email» удалит."
)

SEP = ";"
ENCODING = "utf-8-sig"
EMAIL_COL = "Email"
PAYER_ID_COL = "ID плательщика"


def make_code(email: str) -> str:
  
    """Детерминированный анонимный код: для одного и того же email
    всегда получится один и тот же код (даже в разных файлах/запусках)."""
  
    normalized = str(email).strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]
    return f"PID_{digest}"


def encode_dataframe(df: pd.DataFrame) -> pd.DataFrame:
  
    df = df.copy()

    if EMAIL_COL not in df.columns or PAYER_ID_COL not in df.columns:
        missing = [c for c in (EMAIL_COL, PAYER_ID_COL) if c not in df.columns]
        raise ValueError(f"В файле не найдены столбцы: {', '.join(missing)}")

    df[PAYER_ID_COL] = df[EMAIL_COL].apply(make_code)
    df = df.drop(columns=[EMAIL_COL])
    return df


# состояние
if "encoded_df" not in st.session_state:
    st.session_state.encoded_df = None
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None

uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

if uploaded_file is not None:
    # если загрузили новый файл — сбрасываем предыдущий результат
    if st.session_state.get("uploaded_name") != uploaded_file.name:
        st.session_state.uploaded_name = uploaded_file.name
        st.session_state.encoded_df = None
        try:
            st.session_state.raw_df = pd.read_csv(
                uploaded_file, sep=SEP, encoding=ENCODING
            )
        except Exception as e:
            st.error(f"Не удалось прочитать файл: {e}")
            st.session_state.raw_df = None

    if st.session_state.raw_df is not None:
        st.success(f"Файл загружен: {uploaded_file.name} "
                    f"({len(st.session_state.raw_df)} строк)")

        if st.button("🔐 Закодировать", type="primary"):
            try:
                st.session_state.encoded_df = encode_dataframe(st.session_state.raw_df)
            except Exception as e:
                st.error(f"Ошибка при кодировании: {e}")

if st.session_state.encoded_df is not None:
    st.subheader("Результат")
    st.write("Первые строки обработанного файла:")
    st.dataframe(st.session_state.encoded_df.head(10))

    csv_buffer = io.StringIO()
    st.session_state.encoded_df.to_csv(
        csv_buffer, sep=SEP, index=False, encoding=ENCODING
    )
    csv_bytes = csv_buffer.getvalue().encode(ENCODING)

    out_name = "encoded_" + st.session_state.get("uploaded_name", "result.csv")

    st.download_button(
        label="⬇️ Скачать обработанный файл",
        data=csv_bytes,
        file_name=out_name,
        mime="text/csv",
    )
