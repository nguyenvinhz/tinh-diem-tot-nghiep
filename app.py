import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(page_title="Tính Điểm Xét Tốt Nghiệp THPT 2025", layout="wide")

st.title("Dự Báo Điểm Thi Tối Thiểu Xét Tốt Nghiệp THPT 2025")

st.markdown("""
Ứng dụng này giúp tính toán **điểm trung bình mỗi môn thi tối thiểu** bạn cần đạt để đậu tốt nghiệp dựa trên kết quả học bạ.
*Công thức tính (áp dụng từ 2025):* - Điểm TB 3 năm = `(Lớp 10 + Lớp 11 * 2 + Lớp 12 * 3) / 6`
- Điều kiện đậu: Điểm Xét Tốt Nghiệp $\ge$ 5.0 và không có bài thi nào bị điểm liệt ($\le$ 1.0).
""")

# Upload file
uploaded_file = st.file_uploader("Tải lên file học bạ (CSV, XLSX, hoặc XLS)", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
            if 'Họ và tên' not in df.columns:
                df = pd.read_csv(io.BytesIO(file_bytes), skiprows=1)
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
            if 'Họ và tên' not in df.columns:
                df = pd.read_excel(io.BytesIO(file_bytes), skiprows=1)

        df.columns = df.columns.str.strip()

        if 'Họ và tên' not in df.columns:
            st.error("Không tìm thấy cột 'Họ và tên' trong file. Vui lòng kiểm tra lại cấu trúc file của bạn.")
            st.stop()

        df = df.dropna(subset=['Họ và tên']).reset_index(drop=True)

        required_cols = ['Điểm lớp 10', 'Điểm lớp 11', 'Điểm lớp 12']
        if not all(col in df.columns for col in required_cols):
            st.error(f"File cần chứa các cột: {', '.join(required_cols)}. Các cột hiện có: {list(df.columns)}")
        else:
            df['STT'] = np.arange(1, len(df) + 1)

            df['Điểm TB 3 năm'] = round((df['Điểm lớp 10'] + df['Điểm lớp 11'] * 2 + df['Điểm lớp 12'] * 3) / 6, 2)
            
            st.sidebar.header("Cài đặt Thêm")
            diem_uu_tien = st.sidebar.number_input("Điểm Ưu Tiên (Cộng vào kết quả cuối)", min_value=0.0, max_value=0.5, value=0.0, step=0.25)
            diem_khuyen_khich = st.sidebar.number_input("Tổng Điểm Khuyến Khích (Cho tất cả HS)", min_value=0.0, max_value=4.0, value=0.0, step=0.5)

            df['Tổng 4 môn'] = (10 - 2*diem_uu_tien - df['Điểm TB 3 năm']) * 4 - diem_khuyen_khich
            df['Điểm tối thiểu/môn'] = df['Tổng 4 môn'] / 4
            
            df['Điểm tối thiểu/môn'] = df['Điểm tối thiểu/môn'].apply(lambda x: max(x, 1.25))
            
            def assess_risk(score):
                if score > 10:
                    return "❌ Rớt chắc (Cần > 10 đ/môn, bất khả thi)"
                elif score >= 8.0:
                    return "⚠️ Nguy cơ rất cao (Cần trung bình >= 8.0 đ/môn)"
                elif score >= 5.0:
                    return "🟡 Bình thường (Cần trung bình 5.0 - 8.0 đ/môn)"
                elif score <= 1.25:
                    return "✅ Cực kì an toàn (Chỉ cần tránh điểm liệt <= 1.0)"
                else:
                    return "✅ Khá an toàn (Điểm yêu cầu rất thấp)"

            df['Cảnh báo nguy cơ'] = df['Điểm tối thiểu/môn'].apply(assess_risk)

            display_cols = ['STT', 'Họ và tên', 'Điểm lớp 10', 'Điểm lớp 11', 'Điểm lớp 12', 
                            'Điểm TB 3 năm', 'Điểm tối thiểu/môn', 'Cảnh báo nguy cơ']

            st.subheader("Tải kết quả")
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df[display_cols].to_excel(writer, index=False, sheet_name='Ket_qua')
            
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Tải file kết quả (.xlsx)",
                data=excel_data,
                file_name="KetQua_DuBaoDiemTotNghiep.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.subheader("Bảng tính Điểm Từng Môn Tối Thiểu")
            
            format_dict = {
                'Điểm lớp 10': '{:.2f}',
                'Điểm lớp 11': '{:.2f}',
                'Điểm lớp 12': '{:.2f}',
                'Điểm TB 3 năm': '{:.2f}',
                'Điểm tối thiểu/môn': '{:.2f}'
            }

            st.dataframe(
                df[display_cols].style
                .format(format_dict)
                .map(
                    lambda val: 'color: red' if 'Nguy cơ rất cao' in str(val) or 'Rớt chắc' in str(val) 
                    else ('color: green' if 'an toàn' in str(val) else ''), 
                    subset=['Cảnh báo nguy cơ']
                ),
                hide_index=True 
            )
            
            st.info("""
            💡 **Lưu ý:**
            - **Điểm tối thiểu/môn** hiển thị ở trên là mức điểm mục tiêu *trung bình* bạn cần đạt cho mỗi môn thi. (Ví dụ: Yêu cầu 5.0/môn nghĩa là Toán 4, Văn 6 vẫn được tính là đủ).
            - Thuật toán đã tự động chặn mức thấp nhất là **1.25 điểm**. Dù học bạ của bạn có cao đến đâu, nếu có bất kỳ bài thi nào từ 1.0 điểm trở xuống, bạn vẫn sẽ trượt tốt nghiệp do dính điểm liệt.
            """)
            
    except Exception as e:

        st.error(f"Có lỗi xảy ra khi xử lý file: {e}")
