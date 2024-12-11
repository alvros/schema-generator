import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io
import kaleido
import time

st.set_page_config(
    layout="wide",
    page_title="Alvros Schema Generator",
    page_icon="🌙"
)

# Anpassad CSS för mörkt tema
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #1E1E1E !important; /* Mörkgrå bakgrund */
    color: #E0E0E0; /* Ljus textfärg */
    font-family: "Helvetica", "Arial", sans-serif;
}
            
/* Dölj huvudmenyn (tre prickar) */
#MainMenu {
    display: none;
}

[data-testid="stToolbar"] {
    display: none;
}
/* Sidopanelens bakgrund */
.sidebar .sidebar-content, [data-testid="stSidebar"] {
    background-color: #2A2A2A;
    color: #FFFFFF !important;
}

[data-testid="stSidebar"] * {
    color: #E0E0E0 !important;
}                        

/* Ändra bakgrund och textfärg för input-fält i sidomenyn */
[data-testid="stSidebar"] input, 
[data-testid="stSidebar"] textarea, 
[data-testid="stSidebar"] select {
    background-color: #FFFFFF !important; /* Mörkgrå bakgrund */
    color: #000000 !important;            /* Ljusgrå textfärg */
}            

/* Ändra textfärgen för download-knappar */
[data-testid="stDownloadButton"] button {
    color: #A0A0A0 !important; /* Mörkare textfärg */
    background-color: #3A3A3A !important; /* Samma bakgrundsfärg som andra knappar */
    border: none !important; /* Ingen kantlinje */
}

/* Ändra textfärgen vid hover för download-knappar */
[data-testid="stDownloadButton"] button:hover {
    background-color: #505050 !important; /* Samma hover-bakgrundsfärg */
}

/* Rubriker */
h1 {
    text-align: center;
    color: #FFFFFF;
}  
                      
h2, h3, h4, h5, h6 {
    color: #FFFFFF; /* Vit text för rubriker */
}

/* Kontejnern där innehållsblocken ligger */
.block-container {
    background-color: #1E1E1E;
}

/* Tabeller - ljus text på mörk bakgrund */
table {
    color: #E0E0E0;
}

/* Verktygsrad, header och andra element */
[data-testid="stHeader"] {
    background: #1E1E1E;
    border-bottom: 1px solid #444444; 
}

[data-testid="stToolbar"] {
    background: #1E1E1E;
}

[data-baseweb="tab-highlight"] {
    background: #444444 !important;
}

/* Knappfärger */
.stButton>button {
    background-color: #3A3A3A;
    color: #A0A0A0;
    border: none;
}
.stButton>button:hover {
    background-color: #505050;
}

/* Länkar */
a {
    color: #87CEFA; /* Lugn blå ton för länkar */
}
a:hover {
    color: #ADD8E6; /* Ljusare blå när man hovrar */
}

</style>
""", unsafe_allow_html=True)

# Resten av din kod för appen...


# -----------------------------
# Skiftformsdefinitioner
# -----------------------------
shift_forms = {
    "K5.dag": {
        "cycle_days": 35,
        "segments": [
            {"type": "FM", "days":5, "start":"05:00","end":"14:24"},
            {"type": "Ledig", "days":2},
            {"type": "EM", "days":7, "start":"14:24","end":"00:00"},
            {"type": "Ledig", "days":7},
            {"type": "Dagtid", "days":7, "start":"07:00","end":"16:24"},
            {"type": "Ledig", "days":7}
        ],
        "lags":5
    },
    "K5.natt": {
        "cycle_days": 35,
        "segments": [
            {"type": "FM", "days":5,"start":"06:00","end":"14:36"},
            {"type": "Ledig", "days":2},
            {"type": "EM", "days":7,"start":"14:00","end":"22:36"},
            {"type": "Ledig", "days":7},
            {"type": "Natt", "days": 7, "start": "22:00", "end": "05:00"},
            {"type": "Natt", "days": 7, "start": "05:00", "end": "06:36"},
            {"type": "Ledig", "days":7}
        ],
        "lags":5
    },
    "7/7.fm": {
        "cycle_days":14,
        "segments": [
            {"type":"FM","days":7,"start":"05:00","end":"15:42"},
            {"type":"Ledig","days":7}
        ],
        "lags":2
    },
    "7/7.em": {
        "cycle_days":14,
        "segments": [
            {"type":"EM","days":7,"start":"14:24","end":"00:54"},
            {"type":"Ledig","days":7}
        ],
        "lags":2
    },
    "7/7.natt": {
        "cycle_days":14,
        "segments": [
            {"type":"Natt","days":7,"start":"20:42","end":"05:00"},
            {"type": "Natt", "days": 7, "start": "05:00", "end": "06:36"},
            {"type":"Ledig","days":7}
        ],
        "lags":2
    },
    "7/7.senEM": {
        "cycle_days":14,
        "segments": [
            {"type":"EM","days":7,"start":"15:18","end":"01:00"},
            {"type":"Ledig","days":7}
        ],
        "lags":2
    },
    "7/7.tidEM": {
        "cycle_days":14,
        "segments": [
            {"type":"EM","days":7,"start":"12:18","end":"22:00"},
            {"type":"Ledig","days":7}
        ],
        "lags":2
    },
    "K3": {
        "cycle_days":21,
        "segments": [
            {"type":"FM","days":5,"start":"05:36","end":"14:00"},
            {"type":"Ledig","days":2},
            {"type":"EM","days":7,"start":"13:30","end":"22:30"},
            {"type":"Ledig","days":7}
        ],
        "lags":3
    },
    "Dagtid": {
        "cycle_days":7,
        "segments": [
            {"type":"Dagtid","days":5,"start":"07:00","end":"14:54"},
            {"type":"Ledig","days":2}
        ],
        "lags":1
    }
}

# -----------------------------
# Funktion för att skapa ett 24-timmarsschema utan lag-faktorn
# -----------------------------
def create_24h_schedule(chosen_day, chosen_shift_forms):
    day_start = datetime(chosen_day.year, chosen_day.month, chosen_day.day, 5, 0)
    day_end = day_start + timedelta(hours=24)

    shifts = []
    for (sf_key, people) in chosen_shift_forms:
        sf = shift_forms[sf_key]
        segments = sf["segments"]

        for seg in segments:
            if seg["type"] == "Ledig":
                continue
            start_parts = seg["start"].split(":")
            end_parts = seg["end"].split(":")
            seg_start = day_start.replace(hour=int(start_parts[0]), minute=int(start_parts[1]))
            seg_end = day_start.replace(hour=int(end_parts[0]), minute=int(end_parts[1]))

            if seg_end <= seg_start:
                seg_end += timedelta(days=1)

            if seg_end > day_start and seg_start < day_end:
                adj_start = max(seg_start, day_start)
                adj_end = min(seg_end, day_end)

                shift_category = seg["type"]

                shifts.append({
                    "ShiftForm": sf_key,       # Lägg till skiftformen
                    "ShiftType": seg["type"],
                    "ShiftCategory": shift_category,
                    "Start": adj_start,
                    "End": adj_end,
                    "Employees": people,
                    "ShiftLabel": f"{adj_start.strftime('%H:%M')} - {adj_end.strftime('%H:%M')}"
                })

    return pd.DataFrame(shifts)

def create_24h_gantt(day_shifts_df):
    if day_shifts_df.empty:
        return None

    # Skapa en ny kolumn som kombinerar skiftform och skiftkategori
    day_shifts_df["LineCategory"] = day_shifts_df["ShiftForm"] + " - " + day_shifts_df["ShiftCategory"]

    # Definiera färgkarta (som tidigare)
    color_discrete_map = {
        "K5.dag": "#1f77b4",
        "K5.natt": "#ff7f0e",
        "7/7.fm": "#2ca02c",
        "7/7.em": "#d62728",
        "7/7.natt": "#9467bd",
        "7/7.senEM": "#8c564b",
        "7/7.tidEM": "#e377c2",
        "K3": "#7f7f7f",
        "Dagtid": "#bcbd22"
    }

    fig = px.timeline(
        day_shifts_df,
        x_start="Start",
        x_end="End",
        y="LineCategory",         # Använd nu LineCategory som y
        color="ShiftForm",        # Färgsätt efter skiftform
        text="ShiftLabel",
        hover_data=["Employees"],
        color_discrete_map=color_discrete_map
    )

    fig.update_yaxes(categoryorder="total ascending")
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor='lightgray', 
        side='top', 
        tickformat='%H:%M', 
        dtick=3600000
    )
    fig.update_yaxes(showgrid=True, gridwidth=0.5, gridcolor='lightgray')
    fig.update_traces(textposition='inside', textfont_size=14, textangle=0, insidetextanchor='middle')

    fig.update_layout(
        plot_bgcolor="#2A2A2A",    # Mörkgrå bakgrund innanför diagrammet
        paper_bgcolor="#1E1E1E",   # Samma bakgrund som resten av sidan
        height=400 + len(day_shifts_df["LineCategory"].unique()) * 30,
        margin=dict(t=50, b=80),
        xaxis=dict(tickformat="%H:%M", dtick=3600000),
        legend=dict(
            font=dict(
                color="#E0E0E0"  # Ändra till vit (#FFFFFF) eller ljusgrå (#E0E0E0)
            )
        )
    )

    fig.update_xaxes(
        color="#E0E0E0",     # Ljus textfärg för axelvärden
        gridcolor="#444444"  # Mörkgrå grid-linjer som smälter in
    )

    fig.update_yaxes(
        color="#E0E0E0",     # Ljus textfärg för axelvärden
        gridcolor="#444444",  # Samma grid-linjer som X-axeln
        title_text=''
    )

    # Lås diagrammet mellan 05:00 och 05:00 nästa dag
    day_start = day_shifts_df["Start"].min().replace(hour=5, minute=0)
    day_end = day_start + timedelta(hours=24)
    fig.update_xaxes(range=[day_start, day_end])

    num_shift_categories = len(day_shifts_df["LineCategory"].unique())
    base_height = 400
    height_per_shift = 30
    fig.update_layout(
        height=base_height + num_shift_categories * height_per_shift,
        margin=dict(t=50, b=80),
        xaxis=dict(tickformat="%H:%M", dtick=3600000)
    )

    day_start = day_shifts_df["Start"].min().replace(hour=5, minute=0)
    day_end = day_start + timedelta(hours=24)
    hourly_counts = []
    current_time = day_start
    while current_time < day_end:
        next_hour = current_time + timedelta(hours=1)
        mask = (day_shifts_df["Start"] < next_hour) & (day_shifts_df["End"] > current_time)
        count = day_shifts_df[mask]["Employees"].sum()
        hourly_counts.append({"Time": current_time, "Count": count})
        current_time = next_hour
    hourly_df = pd.DataFrame(hourly_counts)

    for index, row in hourly_df.iterrows():
        fig.add_annotation(
            x=row["Time"] + timedelta(minutes=30),
            y=-0.1,
            text=str(row["Count"]),
            showarrow=False,
            yref="paper",
            xref="x",
            font=dict(color="#E0E0E0", size=12),
            align="center"
        )

    return fig


def export_to_excel(df):
    # Skapa en Excel-fil i minnet
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_save = df.copy()
        df_to_save["Start"] = df_to_save["Start"].dt.strftime("%Y-%m-%d %H:%M")
        df_to_save["End"] = df_to_save["End"].dt.strftime("%Y-%m-%d %H:%M")
        df_to_save.to_excel(writer, sheet_name='Schema', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Schema']

        # Färgmarkera kolumner
        task_format = workbook.add_format({'bg_color': '#FFC7CE'})
        resource_format = workbook.add_format({'bg_color': '#C6EFCE'})

        worksheet.set_column('A:A', 20, task_format)  # ShiftType
        worksheet.set_column('B:B', 25, None)         # ShiftCategory
        worksheet.set_column('C:C', 20, None)         # Start
        worksheet.set_column('D:D', 20, None)         # End
        worksheet.set_column('E:E', 12, resource_format) # Employees
        worksheet.set_column('F:F', 25, None)         # ShiftLabel

    return output.getvalue()

def export_to_excel_gantt(df):
    # Skapa kolumnen LineName
    # LineName = "ShiftForm ShiftType" t.ex. "K5.dag FM"
    df = df.copy()
    df["LineName"] = df["ShiftForm"] + " " + df["ShiftType"]
    # Behåll endast LineName och ShiftLabel
    df = df[["LineName", "ShiftLabel", "ShiftForm", "Start", "End", "Employees"]]

    # Timfönster 05:00 till 05:00 nästa dag
    day_start = df["Start"].min().replace(hour=5, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(hours=24)

    # Färgkarta för skiftformer (samma som i Gantt)
    color_discrete_map = {
        "K5.dag": "#1f77b4",
        "K5.natt": "#ff7f0e",
        "7/7.fm": "#2ca02c",
        "7/7.em": "#d62728",
        "7/7.natt": "#9467bd",
        "7/7.senEM": "#8c564b",
        "7/7.tidEM": "#e377c2",
        "K3": "#7f7f7f",
        "Dagtid": "#bcbd22"
    }

    # Skapa en Excel-fil i minnet
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Skriv enbart LineName och ShiftLabel till Excel, vi lägger till timmar sedan
        minimal_df = df[["LineName", "ShiftLabel"]].copy()
        minimal_df.rename(columns={"LineName": "Skift", "ShiftLabel": "Tider"}, inplace=True)

        minimal_df.to_excel(writer, sheet_name='Schema', index=False)

        workbook = writer.book
        worksheet = writer.sheets['Schema']

        # Justera kolumnbredder
        worksheet.set_column('A:A', 25)  # LineName
        worksheet.set_column('B:B', 20)  # ShiftLabel

        # Lägg till kolumner för timmar
        start_hour = 5
        for i in range(24):
            col_idx = 2 + i
            worksheet.write(0, col_idx, f"{(start_hour + i) % 24}:00")

        # Konvertera Start/End tillbaka till datetime för beräkningar
        df_shift = df.copy()
        df_shift["Start"] = pd.to_datetime(df_shift["Start"])
        df_shift["End"] = pd.to_datetime(df_shift["End"])

        # Skapa ett dictionary av format per ShiftForm baserat på color_discrete_map
        format_map = {}
        for sf, color in color_discrete_map.items():
            format_map[sf] = workbook.add_format({'bg_color': color, 'font_color': '#FFFFFF', 'align': 'center', 'valign': 'vcenter'})

        # Format för standardceller och sum-rad
        default_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})
        sum_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#DDDDDD'})

        # Skriv Gantt-data i timkolumner
        # rad 0 är rubriker, så skiftrader börjar på rad 1
        for row_idx, shift_row in enumerate(df_shift.itertuples(), start=1):
            shift_start = shift_row.Start
            shift_end = shift_row.End
            shift_form = shift_row.ShiftForm
            emp = shift_row.Employees
            hour_format = format_map.get(shift_form, default_format)

            for h in range(24):
                hour_start = day_start + timedelta(hours=h)
                hour_end = hour_start + timedelta(hours=1)

                # Om skiftet överlappar denna timme
                if shift_end > hour_start and shift_start < hour_end:
                    worksheet.write(row_idx, 2 + h, emp, hour_format)
                else:
                    worksheet.write(row_idx, 2 + h, "", default_format)

        # Lägg till en Totalt-rad längst ner
        total_row = 1 + len(df_shift)  # Nästa rad efter sista skift
        worksheet.write(total_row, 0, "Totalt", sum_format)
        worksheet.write(total_row, 1, "", sum_format)  # Ingen ShiftLabel här

        # Summera kolumnvis antal personal
        # Eftersom vi skrivit Employees för aktiva timmar i varje cell,
        # kan vi använda en Excel-formel för att summan av varje kolumn.
        for h in range(24):
            col_letter = chr(ord('A') + 2 + h)  # A=0, B=1 osv. 2 är offset för timmar
            start_cell = f"{col_letter}2"     # första skiftrad
            end_cell = f"{col_letter}{1+len(df_shift)}" # sista skiftrad
            worksheet.write_formula(total_row, 2 + h, f"=SUM({start_cell}:{end_cell})", sum_format)

    return output.getvalue()


def main():
    st.title("24-timmars Schema Generator")

    st.sidebar.header("Inställningar för 24-timmars Gantt Schema")
    chosen_day = datetime(2024,1,1)  # Fast datum
    chosen_forms = st.sidebar.multiselect("Välj skiftformer", list(shift_forms.keys()))

    chosen_shift_forms = []
    for cf in chosen_forms:
        people = st.sidebar.number_input(f"Antal personer för {cf}", min_value=1, value=2, key=f"people_{cf}")
        chosen_shift_forms.append((cf, people))

    if st.sidebar.button("Generera schema"):
        if not chosen_shift_forms:
            st.error("Välj minst en skiftform och ange antal personer.")
        else:
            with st.spinner("Genererar 24-timmarsschema..."):
                day_shifts_df = create_24h_schedule(chosen_day, chosen_shift_forms)
            st.success("24-timmarsschema genererat!")
            
            if day_shifts_df.empty:
                st.warning("Inga aktiva skift under detta dygn.")
            else:
                fig_24h = create_24h_gantt(day_shifts_df)
                if fig_24h:
                    st.plotly_chart(fig_24h, use_container_width=True)

                    unique_id = int(time.time())  # Unikt nummer baserat på aktuellt unix-timestamp

                    # Exportknapp
                    #excel_data = export_to_excel(day_shifts_df)
                    #st.download_button(
                    #    label="Ladda ner Excel-fil",
                    #    data=excel_data,
                    #    file_name=f"24_timmarsschema_{unique_id}.xlsx",
                    #    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    #)

                    # Ny knapp för Excel-Gantt
                    excel_gantt_data = export_to_excel_gantt(day_shifts_df)
                    st.download_button(
                    label="Ladda ner Excel",
                    data=excel_gantt_data,
                    file_name=f"24_timmarsschema_{unique_id}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    # Export till PDF (kräver kaleido)
                    pdf_bytes = fig_24h.to_image(format="pdf")
                    st.download_button(
                        label="Ladda ner PDF",
                        data=pdf_bytes,
                        file_name=f"24_timmarsschema_{unique_id}.pdf",
                        mime="application/pdf"
                    )

# Lägg till footer
    st.markdown("""
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #1E1E1E;
        color: #E0E0E0;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        box-shadow: 0 -1px 5px rgba(0,0,0,0.3);
    }
    .footer a {
        color: #87CEFA;
        text-decoration: none;
        margin: 0 10px;
    }
    .footer a:hover {
        text-decoration: underline;
    }
    @media (max-width: 600px) {
        .footer {
            font-size: 12px;
            padding: 8px;
        }
        .footer a {
            margin: 0 5px;
        }
    }
    </style>
    <div class="footer">
        Applikation skapad av <strong>Fredrik Alvros</strong>. 2024 Kontakta via 
        <a href="mailto:fredrik.alvros@lkab.com">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/new-post.png" alt="Email" style="vertical-align: middle;"/> Email
        </a>  
        <a href="https://www.linkedin.com/in/karl-fredrik-alvros/" target="_blank">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/linkedin.png" alt="LinkedIn" style="vertical-align: middle;"/> LinkedIn
        </a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()