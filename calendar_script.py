from datetime import datetime, date, timedelta
from fpdf import FPDF
from icalendar import Calendar
import requests
import streamlit as st

def get_ical_data(ical_url):
    try:
        response = requests.get(ical_url)
        response.raise_for_status()

        cal = Calendar.from_ical(response.text)
        return cal
    except requests.exceptions.RequestException as e:
        print(f"Error fetching iCalendar data: {e}")
        return None
    except Exception as e:
        print(f"Error parsing iCalendar data: {e}")
        return None

ical_url = st.secrets["cal_url"]
calendar = get_ical_data(ical_url)

pdf = FPDF()
pdf.add_page()
pdf.set_xy(0, 0)

st.set_page_config(page_title="Majalis Schedule Generator", layout="centered")
st.title("Majalis Schedule Generator")

preset = st.radio("Select date range:", [
    "All dates",
    "Today only",
    "Next 7 days",
    "Next 30 days",
    "This month",
    "Next month"
])

today = date.today()
start_date, end_date = None, None

if preset == "Today only":
    start_date = today
    end_date = today
elif preset == "Next 7 days":
    start_date = today
    end_date = today + timedelta(days=7)
elif preset == "Next 30 days":
    start_date = today
    end_date = today + timedelta(days=30)
elif preset == "This month":
    start_date = date(today.year, today.month, 1)
    end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
elif preset == "Next month":
    next_month = today.month + 1 if today.month < 12 else 1
    year = today.year if today.month < 12 else today.year + 1
    start_date = date(year, next_month, 1)
    end_date = date(year, next_month + 1, 1) - timedelta(days=1)

# Display selected range
if preset != "All dates":
    range_text = f"Showing events from {start_date.strftime('%b %d, %Y')}"
    if end_date != start_date:
        range_text += f" to {end_date.strftime('%b %d, %Y')}"
    st.info(range_text)


if st.button("Generate PDF"):
    if calendar:
        with st.spinner('Generating PDF...'):
            events = []
            for component in calendar.walk():
                if component.name == "VEVENT":
                    summary = component.get('SUMMARY')
                    start_time = component.get('DTSTART').dt
                    if isinstance(start_time, datetime):  # Make sure it's a datetime object
                        event_date = start_time.date() if isinstance(start_time, datetime) else start_time
                        if (not start_date or event_date >= start_date) and \
                            (not end_date or event_date <= end_date):
                            events.append((start_time, component))

            events.sort(key=lambda x: x[0])

            pdf.set_font('arial', 'B', 13.0)
            pdf.cell(0, 10, align='C', txt="Majalis List 2025\n")
            pdf.ln(7)
            pdf.set_font('arial', 'B', 11.0)
            pdf.cell(0, 10, f"From {start_date.strftime('%b %d, %Y') if start_date else 'the beginning'} to {end_date.strftime('%b %d, %Y') if end_date else 'the end'}")
            pdf.ln(7)
            pdf.set_font('arial', '', 11.0)

            for start_time, event in events:
                pdf.cell(0, 6, f"Host: {event.get('summary')}", ln=1)
                pdf.cell(0, 6, f"Date: {start_time.strftime('%A %B %d %Y')}", ln=1)
                pdf.cell(0, 6, f"Time: {start_time.strftime('%I:%M %p')}", ln=1)
                location = event.get('location')
                if location: # optional param
                    pdf.cell(0, 6, f"Location: {location}", ln=1)
                pdf.ln(3)

            pdf_bytes = pdf.output(dest='S')
            st.success("PDF generated successfully!")
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name="majalis_schedule.pdf",
                mime="application/pdf"
            )