from flask import Flask, render_template, request, send_file, jsonify
import ipaddress
import io
from fpdf import FPDF
import os

# Wymuszenie obsługi UTF-8
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

app = Flask(__name__)

# Funkcja do obliczania VLSM
def calculate_vlsm(network, hosts):
    hosts = sorted(hosts, reverse=True)  # Sortowanie hostów malejąco
    subnets = []
    current_address = network.network_address  # Start od adresu sieci

    total_required_addresses = sum(2 ** (32 - (32 - (h + 2 - 1).bit_length())) for h in hosts)
    available_addresses = network.num_addresses

    if total_required_addresses > available_addresses:
        return None, f"⚠️ Wymagana liczba adresów ({total_required_addresses}) przekracza dostępny zakres {network}. Proszę dostosować adres i maskę."

    try:
        for h in hosts:
            needed_hosts = h + 2
            new_prefix = 32 - (needed_hosts - 1).bit_length()

            subnet = ipaddress.ip_network(f"{current_address}/{new_prefix}", strict=False)
            if subnet.broadcast_address > network.broadcast_address:
                return None, f"⚠️ Nie można przydzielić {h} hostów w sieci {network}. Proszę dostosować adres i maskę."

            subnet_info = {
                'network_address': f"{subnet.network_address}/{subnet.prefixlen}",
                'broadcast_address': str(subnet.broadcast_address),
                'first_host': str(subnet.network_address + 1),
                'last_host': str(subnet.broadcast_address - 1),
                'total_hosts': subnet.num_addresses - 2
            }

            subnets.append(subnet_info)
            current_address = subnet.broadcast_address + 1
    except Exception as e:
        raise ValueError(f'Błąd przy obliczaniu VLSM: {str(e)}')

    return subnets, None

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    error_message = None
    if request.method == 'POST':
        network = request.form.get('network')
        hosts = request.form.get('hosts')
        try:
            network = ipaddress.ip_network(network, strict=False)
            hosts = list(map(int, hosts.split(',')))
            results, error_message = calculate_vlsm(network, hosts)
        except ValueError as e:
            error_message = f'Błąd: {str(e)}'
        except Exception as e:
            error_message = f'Nieznany błąd: {str(e)}'

    return render_template('index.html', results=results, error_message=error_message)

@app.route('/export_txt', methods=['POST'])
def export_txt():
    try:
        # Pobranie danych z formularza
        data = request.form.get('data')
        if not data:
            return "Brak danych do wygenerowania pliku TXT.", 400

        # Konwersja danych na UTF-8 (jeśli potrzebne)
        data = data.encode('utf-8').decode('utf-8')

        # Tworzenie pliku TXT w pamięci
        output = io.StringIO()
        output.write(data)
        output.seek(0)

        # Wysyłanie pliku do użytkownika
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/plain',
            as_attachment=True,
            download_name='vlsm_results.txt'
        )
    except Exception as e:
        return f"Błąd podczas generowania pliku TXT: {str(e)}", 500

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.form.get('data')
        if not data:
            return "Brak danych do wygenerowania PDF.", 400

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Dodanie czcionek Unicode
        font_path = os.path.join("static", "fonts", "DejaVuSans.ttf")
        bold_font_path = os.path.join("static", "fonts", "DejaVuSans-Bold.ttf")

        print("Pliki w katalogu fonts:", os.listdir("./static/fonts"))  # Debug

        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.add_font("DejaVu", "B", bold_font_path, uni=True)

        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.set_auto_page_break(auto=True, margin=10)

        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 10, "Wyniki Podziału Sieci (VLSM)", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("DejaVu", "", 12)
        pdf.cell(0, 10, "Test polskich znaków: ąćęłńóśźż", ln=True, align="L")
        pdf.ln(10)

        lines = data.splitlines()
        for line in lines:
            line = line.strip().encode('utf-8').decode('utf-8')  # Wymuszenie UTF-8

            if line.startswith("Podsieć"):
                pdf.set_font("DejaVu", "B", 12)
                pdf.multi_cell(190, 8, txt=line, align="L")
            else:
                pdf.set_font("DejaVu", "", 12)
                pdf.multi_cell(190, 8, txt=line, align="L")

            pdf.ln(1)

        output = io.BytesIO()
        pdf.output(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="vlsm_results.pdf",
        )
    except Exception as e:
        return f"Błąd podczas generowania pliku PDF: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
