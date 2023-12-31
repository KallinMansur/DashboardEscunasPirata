import http.server
import socketserver
import threading
import webbrowser

from bs4 import BeautifulSoup
import requests
import time

# Global variable to store the last table content
last_table_content = None

def get_table_content(url):
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')

        if table:
            # Extract table content as a list of lists
            table_data = [[cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])] for row in table.find_all('tr')]
            return table_data
        else:
            return None
    else:
        return None

def create_html_table(table_content):
    header_html = """
        <header>
            <img src="https://escunaspirata.com.br/wp-content/uploads/2021/10/logohorizontal.png" alt="Logo">
        </header>
    """

    table_rows = create_table_rows(table_content)

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Ao Vivo - Escunas Pirata</title>
        <link rel="icon" type="image/png" href="https://escunaspirata.com.br/wp-content/uploads/2021/10/cropped-LOGORESPONSIVA-192x192-1-150x150.png">
        <style>
            body {{
                font-family: 'Arial', sans-serif;
                background-color: #f0f0f0;
                margin: 0;
                padding: 0;
            }}

            header {{
                background-color: #fcc23d;
                color: #fff;
                text-align: center;
                padding: 10px;
                height: 174px;
                overflow: hidden;
            }}

            header img {{
                max-height: 100%;
                width: auto;
            }}

            table {{
                margin: 20px;
                border-collapse: collapse;
                width: calc(100% - 40px);
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}

            th {{
                background-color: #333;
                color: #fff;
            }}

            tr:hover {{
                background-color: #f5f5f5;
            }}

            td {{
                font-weight: bold;
                font-size: larger;
            }}
        </style>
    </head>
    <body>
        {header_html}
        <table>
            {table_rows}
        </table>
        <script>
            function refreshTable() {{
                // Fetch the table content from the local server
                fetch('http://localhost:8000')
                    .then(response => response.text())
                    .then(data => {{
                        // Create a temporary element to parse the fetched HTML content
                        const tempElement = document.createElement('div');
                        tempElement.innerHTML = data;

                        // Extract the table content
                        const tableContent = tempElement.querySelector('table').innerHTML;

                        // Update the content of the table container
                        document.querySelector('table').innerHTML = tableContent;
                    }})
                    .catch(error => console.error('Error:', error));
            }}

            // Initial load of the table content
            refreshTable();

            // Set up a timer to refresh the table every 15 seconds
            setInterval(refreshTable, 15000);
        </script>
    </body>
    </html>
    """

    return html_content

def create_table_rows(table_content):
    global last_table_content  # Use the global variable

    if last_table_content is None:
        # If last_table_content is not initialized, set it to the current table content
        last_table_content = table_content

    # Sort the remaining rows by the first column and then by the second column
    sorted_rows = sorted(table_content[2:], key=lambda x: (x[0], x[1]))

    rows = ""

    # Create the first row with merged cells
    rows += "<tr>"
    rows += "<td colspan='1'>{}</td>".format(table_content[0][0])
    rows += "<td colspan='1'>{}</td>".format(table_content[0][1])
    rows += "<td colspan='1'>{}</td>".format(table_content[0][2])
    rows += "<td colspan='2'>{}</td>".format(table_content[0][3])
    rows += "<td colspan='2'>{}</td>".format(table_content[0][4])
    rows += "<td colspan='2'>{}</td>".format(table_content[0][5])
    rows += "</tr>"

    # Create the second row starting from the third cell
    rows += "<tr>"
    rows += "<td colspan='2'></td>"
    for cell_data, last_value in zip(table_content[1][:], last_table_content[1][:]):
        # Change cell color to green if the value has changed
        style = "color: green;" if cell_data != last_value else ""
        rows += f"<td style='{style}'>{cell_data}</td>"
    rows += "</tr>"

    # Create the sorted remaining rows
    for row_data, last_row_data in zip(sorted_rows, last_table_content[2:]):
        rows += "<tr>"
        for i, (cell_data, last_value) in enumerate(zip(row_data, last_row_data)):
            # Change cell color to green if the value has changed
            style = "color: green;" if cell_data != last_value else ""

            # Apply background color to the eighth column based on its values
            if i == 7:  # Eighth column
                cell_value = int(cell_data) if cell_data.isdigit() else 0
                if cell_value >= 150:
                    style += "background-color: red;"
                elif cell_value >= 135:
                    style += "background-color: orange;"
                elif cell_value >= 120:
                    style += "background-color: yellow;"

            rows += f"<td style='{style}'>{cell_data}</td>"
        rows += "</tr>"

    last_table_content = None

    last_table_content = table_content[0:2][:]
    for row in sorted_rows:
        last_table_content.append(row)

    return rows


def start_server(table_url, port=8000):
    class RequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                # Fetch table content
                table_content = get_table_content(table_url)

                if table_content:
                    # Create HTML table
                    html_table = create_html_table(table_content)

                    # Send HTML response
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(html_table.encode())
                else:
                    self.send_response(500)

    # Start the server in a separate thread
    server = socketserver.TCPServer(('localhost', port), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Open the default web browser
    webbrowser.open(f'http://localhost:{port}')

    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C to stop the server
        server.shutdown()
        server.server_close()
        print("\nServer stopped.")

if __name__ == "__main__":
    # URL of the webpage
    url = "https://escunaspirata.com.br/aovivo/"

    # Start the server with the specified URL
    start_server(url)
