import streamlit as st
import cv2
import time
from pyzbar.pyzbar import decode
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build


credentials_info = {
    "type": st.secrets["GOOGLE_TYPE"],
    "project_id": st.secrets["GOOGLE_PROJECT_ID"],
    "private_key_id": st.secrets["GOOGLE_PRIVATE_KEY_ID"],
    "private_key": st.secrets["GOOGLE_PRIVATE_KEY"],
    "client_email": st.secrets["GOOGLE_CLIENT_EMAIL"],
    "client_id": st.secrets["GOOGLE_CLIENT_ID"],
    "auth_uri": st.secrets["GOOGLE_AUTH_URI"],
    "token_uri": st.secrets["GOOGLE_TOKEN_URI"],
    "auth_provider_x509_cert_url": st.secrets["GOOGLE_AUTH_PROVIDER_X509_CERT_URL"],
    "client_x509_cert_url": st.secrets["GOOGLE_CLIENT_X509_CERT_URL"],
    "universe_domain": st.secrets["GOOGLE_UNIVERSE_DOMAIN"],
}

def scan_qr_code():
    cap = cv2.VideoCapture(0)  # Open the camera
    scanned_data = None
    # Create a container to hold the video feed
    video_feed = st.empty()
    
    # Continue to read frames until QR code is detected or user stops
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to access the webcam.")
            break

        # Convert the frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mirrored_frame = cv2.flip(frame_rgb, 1)

        # Display the frame in Streamlit
        video_feed.image(mirrored_frame, caption="Scanning for QR Code...", channels="RGB")

        # Decode the QR code from the frame
        qr_codes = decode(frame)
        for qr_code in qr_codes:
            scanned_data = qr_code.data.decode('utf-8')
            cap.release()  # Release the camera
            video_feed.empty()  # Remove the video feed
            st.success("QR Code scanned successfully! ✅")
            return scanned_data
        
        # Slight delay for smoother processing
        time.sleep(0.01)

    cap.release()  # Release the camera
    video_feed.empty()  # Remove the video feed
    return scanned_data

def connect_to_google_sheets(sheet_id, range_name):
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
    return result.get('values', [])

def update_google_sheets(sheet_id, range_name, values):
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    service = build('sheets', 'v4', credentials=credentials)
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption='RAW', body=body).execute()
    return result.get('updatedCells')

st.title("QR Code RSVP Confirmation")

gift_received = st.checkbox("Gift")
if st.button('Start scan'):
    qr_data = scan_qr_code()
    with st.spinner('Processing Data...'):
        if qr_data:
            st.write(f"QR Code Data: {qr_data}")
            sheet_id = '1ZGcOvcpP5JlWyxLRyoLkUR_kreC46UeinU0KiKlBSJ8'
            guest_sheet_range = 'Sheet1!A2:G100'
            guests = connect_to_google_sheets(sheet_id, guest_sheet_range)
            for i, guest in enumerate(guests):
                if guest and guest[0] == qr_data:
                    if len(guests[i]) >= 7:
                        guest[5] = 'Confirmed'
                        guest[6] = 'Yes' if gift_received else 'No'
                    else:
                        st.error('Incomplete Guest Data')
                    update_google_sheets(sheet_id, guest_sheet_range, guests)
                    st.success("RSVP Confirmed")
                    break
            else:
                st.error("Guest Not Found")
        else:
            st.error("QR Scan Failed")
