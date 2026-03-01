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

uploaded_file = st.file_uploader("Tải lên file học bạ (CSV, XLSX, hoặc XLS)", type=['csv', 'xlsx', 'xls'])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        is_csv = uploaded_file.name.lower().endswith('.csv')
        
        df = None
        # 1. Quét tìm dòng tiêu đề chuẩn
        for skip in range(6):
            try:
                if is_csv:
                    temp_df = pd.read_csv(io.BytesIO(file_bytes), skiprows=skip)
                else:
                    temp_df = pd.read_excel(io.BytesIO(file_bytes), skiprows=skip)
                
                temp_df.columns = temp_df.columns.astype(str).str.strip()
                
                name_col = None
                for col in temp_df.columns:
                    col_lower = str(col).lower()
                    if col_lower in ['họ và tên', 'họ tên', 'tên', 'ho va ten', 'ho ten', 'name']:
                        name_col = col
                        break
                
                if name_col:
                    temp_df.rename(columns={name_col: 'Họ và tên'}, inplace=True)
                    df = temp_df
                    break
            except Exception:
                continue

        if df is None:
            st.error("Không tìm thấy cột chứa Tên học sinh (Họ và tên, Họ tên, Tên...). Vui lòng kiểm tra lại file của bạn.")
            st.stop()

        # --- HIỂN THỊ DỮ LIỆU GỐC ---
        with st.expander("👀 Xem dữ liệu gốc (Bấm để mở rộng/thu gọn)"):
            st.dataframe(df)

        # --- XÓA CÁC DÒNG RỖNG VÀ DÒNG THỐNG KÊ (Tổng cộng, Tỉ lệ...) ---
        df = df.dropna(subset=['Họ và tên'])
        
        # Lọc bỏ các dòng mà tên bắt đầu bằng "Tổng", "Tỉ lệ", "Trung bình"...
        invalid_prefixes = ('tổng', 'tỉ lệ', 'ty le', 'trung bình', 'ghi chú', 'tb')
        df = df[~df['Họ và tên'].astype(str).str.lower().str.startswith(invalid_prefixes)]
        
        df = df.reset_index(drop=True)
        df['STT'] = np.arange(1, len(df) + 1)

        display_cols = ['STT', 'Họ và tên']
        format_dict = {}

        # 2. XỬ LÝ LINH HOẠT CÁC CỘT ĐIỂM (3 cột hoặc 1 cột ĐTB)
        col_10 = next((c for c in df.columns if '10' in str(c)), None)
        col_11 = next((c for c in df.columns if '11' in str(c)), None)
        col_12 = next((c for c in df.columns if '12' in str(c)), None)
        
        col_dtb = next((c for c in df.columns if any(x in str(c).lower() for x in ['tb', 'trung bình', 'đtb'])), None)

        has_3_years = bool(col_10 and col_11 and col_12)

        if has_3_years:
            # Ưu tiên tính lại bằng công thức chuẩn 2025 để đảm bảo độ chính xác
            df[col_10] = pd.to_numeric(df[col_10], errors='coerce').fillna(0)
            df[col_11] = pd.to_numeric(df[col_11], errors='coerce').fillna(0)
            df[col_12] = pd.to_numeric(df[col_12], errors='coerce').fillna(0)
            
            df['Điểm TB 3 năm'] = round((df[col_10] + df[col_11] * 2 + df[col_12] * 3) / 6, 2)
            
            display_cols.extend([col_10, col_11, col_12, 'Điểm TB 3 năm'])
            format_dict.update({
                col_10: '{:.2f}', col_11: '{:.2f}', col_12: '{:.2f}', 'Điểm TB 3 năm': '{:.2f}'
            })
        elif col_dtb:
            df['Điểm TB 3 năm'] = pd.to_numeric(df[col_dtb], errors='coerce').fillna(0)
            df['Điểm TB 3 năm'] = round(df['Điểm TB 3 năm'], 2)
            
            display_cols.append('Điểm TB 3 năm')
            format_dict['Điểm TB 3 năm'] = '{:.2f}'
        else:
            st.error("File cần chứa các cột điểm: Hoặc đủ 3 năm (lớp 10, lớp 11, lớp 12) HOẶC cột Điểm trung bình (ĐTB, Điểm TB...).")
            st.stop()

        # 3. XỬ LÝ ĐỘNG CỘT ƯU TIÊN VÀ KHUYẾN KHÍCH
        ut_cols = [col for col in df.columns if 'ưu tiên' in str(col).lower()]
        if ut_cols:
            df['Điểm ƯT'] = pd.to_numeric(df[ut_cols[0]], errors='coerce').fillna(0)
            display_cols.append('Điểm ƯT')
            format_dict['Điểm ƯT'] = '{:.2f}'
        else:
            df['Điểm ƯT'] = 0.0
            
        kk_cols = [col for col in df.columns if 'khuyến khích' in str(col).lower()]
        if kk_cols:
            df['Điểm KK'] = pd.to_numeric(df[kk_cols[0]], errors='coerce').fillna(0)
            display_cols.append('Điểm KK')
            format_dict['Điểm KK'] = '{:.2f}'
        else:
            df['Điểm KK'] = 0.0
            
        # 4. TÍNH TOÁN
        df['Tổng 4 môn'] = (10 - 2 * df['Điểm ƯT'] - df['Điểm TB 3 năm']) * 4 - df['Điểm KK']
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

        display_cols.extend(['Điểm tối thiểu/môn', 'Cảnh báo nguy cơ'])
        format_dict['Điểm tối thiểu/môn'] = '{:.2f}'

        # 5. TẢI XUỐNG VÀ HIỂN THỊ
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
        - Hệ thống thông minh tự nhận diện nếu file có 3 cột điểm (10, 11, 12) hoặc 1 cột Điểm trung bình (ĐTB). Nếu có đủ 3 năm, hệ thống tự động gộp và tính trung bình theo công thức 2025.
        - Tự động nhận diện cột **'Ưu tiên'** hoặc **'Khuyến khích'** (nếu có).
        - Thuật toán đã tự động chặn mức thấp nhất là **1.25 điểm** (bảo vệ học sinh khỏi mức điểm liệt $\le$ 1.0).
        """)
            
    except Exception as e:
        st.error(f"Có lỗi xảy ra khi xử lý file: {e}")
