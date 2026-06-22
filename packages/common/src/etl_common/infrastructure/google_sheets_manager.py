import logging
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    def __init__(self, credentials_file: str, token_file: str, scopes: list[str]):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.sheets_service = None
        self.drive_service = None

    def connect(self):
        """Conecta a la API de Google Sheets."""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}")

        try:
            creds = None

            # Verificar token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes)
            # Si no hay credenciales válidas, solicitar al usuario que inicie sesión
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes
                    )
                    creds = flow.run_local_server(port=0)
                # Guardar credenciales para la próxima ejecución
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())

            # Construir servicios
            self.sheets_service = build('sheets', 'v4', credentials=creds)
            self.drive_service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Connected to Google Sheets API")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Google Sheets API: {e}")
            raise

    def get_spreadsheet_id_by_name(self, name: str) -> str:
        """Finds a spreadsheet ID by its name."""
        try:
            results = self.drive_service.files().list(
                q=f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet'",
                spaces='drive',
                fields='files(id, name)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            if not files:
                return None
            return files[0]['id']
        except Exception as e:
            logger.error(f"❌ Error searching for spreadsheet '{name}': {e}")
            raise

    def get_worksheet_id(self, spreadsheet_id: str, worksheet_name: str) -> int:
        """Obtiene el ID de una hoja de cálculo por su nombre."""
        try:
            sheet_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id).execute()
            sheets = sheet_metadata.get('sheets', [])
            for sheet in sheets:
                if sheet['properties']['title'] == worksheet_name:
                    return sheet['properties']['sheetId']
            return None
        except Exception as e:
            logger.error(
                f"❌ Error getting worksheet ID for '{worksheet_name}': {e}")
            raise

    def create_worksheet(self, spreadsheet_id: str, title: str, row_count: int = 20000, col_count: int = 37) -> int:
        """Crea una nueva worksheet."""
        try:
            request = {
                'addSheet': {
                    'properties': {
                        'title': title,
                        'gridProperties': {
                            'rowCount': row_count,
                            'columnCount': col_count
                        }
                    }
                }
            }
            response = self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()

            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            logger.info(f"✅ Created new worksheet: {title} (ID: {sheet_id})")
            return sheet_id
        except Exception as e:
            logger.error(f"❌ Error creating worksheet '{title}': {e}")
            raise

    def resize_worksheet(self, spreadsheet_id: str, worksheet_id: int, row_count: int = 20000, col_count: int = 37):
        """Redimensiona una worksheet."""
        try:
            request = {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': worksheet_id,
                        'gridProperties': {
                            'rowCount': row_count,
                            'columnCount': col_count
                        }
                    },
                    'fields': 'gridProperties'
                }
            }
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': [request]}
            ).execute()
            logger.info(
                f"✅ Resized worksheet {worksheet_id} to {row_count} rows")
        except Exception as e:
            logger.error(f"❌ Error resizing worksheet {worksheet_id}: {e}")
            raise

    def clear_range(self, spreadsheet_id: str, range_name: str):
        """Limpia un rango en una spreadsheet."""
        try:
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
        except Exception as e:
            logger.error(f"❌ Error clearing range '{range_name}': {e}")
            raise

    def write_values(self, spreadsheet_id: str, range_name: str, values: list[list], value_input_option: str = 'RAW'):
        """Escribe valores en un rango."""
        try:
            body = {'values': values}
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            return result
        except Exception as e:
            logger.error(f"❌ Error writing to '{range_name}': {e}")
            raise

    def read_sheet(self, spreadsheet_id: str, range_name: str):
        """Lee valores de un rango."""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            return result.get('values', [])
        except Exception as e:
            logger.error(f"❌ Error reading from '{range_name}': {e}")
            raise

    def ensure_worksheet(self, spreadsheet_id: str, worksheet_name: str, row_count: int = 20000):
        """Asegura que una worksheet exista y tenga el tamaño correcto. Limpia si ya existe."""
        worksheet_id = self.get_worksheet_id(spreadsheet_id, worksheet_name)

        if worksheet_id is None:
            logger.info(
                f"📝 Worksheet '{worksheet_name}' not found. Creating...")
            self.create_worksheet(spreadsheet_id, worksheet_name, row_count)
        else:
            logger.info(f"📝 Worksheet '{worksheet_name}' found. Resizing...")
            self.resize_worksheet(spreadsheet_id, worksheet_id, row_count)

        self.clear_range(spreadsheet_id, f"'{worksheet_name}'!A:Z")
