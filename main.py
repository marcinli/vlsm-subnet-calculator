from flask import Flask, render_template, request, send_file, jsonify
import ipaddress
import io
from fpdf import FPDF
import os
os.environ["LC_ALL"] = "en_US.UTF-8"
os.environ["LANG"] = "en_US.UTF-8"

app = Flask(__name__)

# Funkcja do obliczania VLSM
def calculate_vlsm(network, hosts):
    hosts = sorted(hosts, reverse=True)  # Sortowanie hostów malejąco
    subnets = []
    current_address = network.network_address  # Start od adresu sieci

    # Obliczanie całkowitej liczby wymaganych adresów (uwzględniając VLSM)
    total_required_addresses = sum(2 ** (32 - (32 - (h + 2 - 1).bit_length())) for h in hosts)
    available_addresses = network.num_addresses  # Liczba dostępnych adresów w sieci

    # Jeśli wymagane adresy przekraczają dostępne – natychmiastowy błąd
    if total_required_addresses > available_addresses:
        return None, f"⚠️ Wymagana liczba adresów ({total_required_addresses}) przekracza dostępny zakres {network}. Proszę dostosować adres i maskę."

    try:
        for h in hosts:
            needed_hosts = h + 2  # hosty + adres sieci + broadcast
            new_prefix = 32 - (needed_hosts - 1).bit_length()

            # Obliczanie nowej podsieci
            subnet = ipaddress.ip_network(f"{current_address}/{new_prefix}", strict=False)

            # Jeśli podsieć przekracza zakres sieci bazowej – błąd
            if subnet.broadcast_address > network.broadcast_address:
                return None, f"⚠️ Nie można przydzielić {h} hostów w sieci {network}. Proszę dostosować adres i maskę."

            # Szczegółowe informacje o podsieci
            subnet_info = {
                'network_address': f"{subnet.network_address}/{subnet.prefixlen}",
                'broadcast_address': str(subnet.broadcast_address),
                'first_host': str(subnet.network_address + 1),
                'last_host': str(subnet.broadcast_address - 1),
                'total_hosts': subnet.num_addresses - 2
            }

            subnets.append(subnet_info)
            current_address = subnet.broadcast_address + 1  # Przesunięcie do następnej sieci
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
    data = request.form.get('data')
    file = io.StringIO()
    file.write(data)
    file.seek(0)

    return send_file(
        io.BytesIO(file.getvalue().encode()),
        mimetype='text/plain',
        as_attachment=True,
        download_name='vlsm_results.txt'
    )


@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    try:
        data = request.form.get('data')
        if not data:
            return "Brak danych do wygenerowania PDF.", 400

        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Dodanie niestandardowych czcionek Unicode
        pdf.add_font("DejaVu", "", "./static/fonts/DejaVuSans.ttf", uni=True)
        pdf.add_font("DejaVu", "B", "./static/fonts/DejaVuSans-Bold.ttf", uni=True)

        # Ustawienia marginesów i szerokości
        left_margin = 10
        right_margin = 10
        page_width = 210  # Szerokość strony A4 w mm
        effective_width = page_width - left_margin - right_margin

        pdf.set_left_margin(left_margin)
        pdf.set_right_margin(right_margin)
        pdf.set_auto_page_break(auto=True, margin=10)

        # Dodanie tytułu dokumentu
        pdf.set_font("DejaVu", "B", 14)  # Pogrubiona czcionka
        pdf.cell(0, 10, "Wyniki Podziału Sieci (VLSM)", ln=True, align="C")
        pdf.ln(10)  # Odstęp po tytule

        # Przetwarzanie danych
        lines = data.splitlines()
        for line in lines:
            line = line.strip()

            # Ustawienie czcionki i dynamiczne łamanie linii
            if line.startswith("Podsieć"):
                pdf.set_font("DejaVu", "B", 12)  # Pogrubiona czcionka
                pdf.multi_cell(effective_width, 8, txt=line, align="L")  # Nagłówki
            else:
                pdf.set_font("DejaVu", "", 12)  # Normalna czcionka
                pdf.multi_cell(effective_width, 8, txt=line, align="L")  # Dane

            pdf.ln(1)  # Drobny odstęp między liniami

        # Zapisanie PDF w pamięci
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






@app.route('/validate', methods=['POST'])
def validate():
    try:
        network = request.json.get('network')
        hosts = request.json.get('hosts')

        # Walidacja adresu IP
        ipaddress.ip_network(network, strict=False)

        # Walidacja hostów
        for h in hosts:
            if not isinstance(h, int) or h <= 0:
                return jsonify({"error": f"Niewłaściwa liczba hostów: {h}"}), 400

        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
