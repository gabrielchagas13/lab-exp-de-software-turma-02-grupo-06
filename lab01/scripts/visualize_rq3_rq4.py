import argparse
import csv
import os

try:
    import matplotlib.pyplot as plt
except ImportError:
    print("Erro: matplotlib não encontrado. Instale com: pip install matplotlib")
    exit(1)

def load_rows(input_path: str) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def to_number(value: str):
    if value in (None, ""):
        return None
    return float(value)

def generate_charts(rows: list[dict], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    # Categorias RQ03
    cat_rq3 = {"0": 0, "1-99": 0, "100-999": 0, "1000 (teto)": 0}
    # Categorias RQ04
    cat_rq4 = {"0 dias (hoje)": 0, "1-30 dias": 0, "31-365 dias": 0, "> 365 dias": 0}
    
    for row in rows:
        r_val = to_number(row.get("total_releases"))
        d_val = to_number(row.get("days_since_update"))
        
        if r_val is not None:
            if r_val == 0:
                cat_rq3["0"] += 1
            elif r_val < 100:
                cat_rq3["1-99"] += 1
            elif r_val < 1000:
                cat_rq3["100-999"] += 1
            else:
                cat_rq3["1000 (teto)"] += 1
                
        if d_val is not None:
            if d_val == 0:
                cat_rq4["0 dias (hoje)"] += 1
            elif d_val <= 30:
                cat_rq4["1-30 dias"] += 1
            elif d_val <= 365:
                cat_rq4["31-365 dias"] += 1
            else:
                cat_rq4["> 365 dias"] += 1

    # Gráfico RQ03
    plt.figure(figsize=(8, 5))
    plt.bar(cat_rq3.keys(), cat_rq3.values(), color='#4C72B0')
    plt.title('RQ03 - Distribuição de Releases', fontsize=14)
    plt.xlabel('Quantidade de Releases', fontsize=12)
    plt.ylabel('Número de Repositórios', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    for i, v in enumerate(cat_rq3.values()):
        plt.text(i, v + 5, str(v), ha='center', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rq03_releases.svg'), format='svg')
    plt.close()
    
    # Gráfico RQ04
    plt.figure(figsize=(8, 5))
    plt.bar(cat_rq4.keys(), cat_rq4.values(), color='#55A868')
    plt.title('RQ04 - Tempo desde Última Atualização', fontsize=14)
    plt.xlabel('Faixa de tempo (dias)', fontsize=12)
    plt.ylabel('Número de Repositórios', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    for i, v in enumerate(cat_rq4.values()):
        plt.text(i, v + 5, str(v), ha='center', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rq04_updates.svg'), format='svg')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Gera graficos para RQ03 e RQ04")
    parser.add_argument("--input", default="data/repos_1000.csv", help="CSV de entrada")
    parser.add_argument("--output-dir", default="docs/img", help="Diretório de saída para as imagens")
    args = parser.parse_args()
    
    rows = load_rows(args.input)
    generate_charts(rows, args.output_dir)
    print(f"Gráficos gerados com sucesso no diretório '{args.output_dir}'")

if __name__ == "__main__":
    main()
