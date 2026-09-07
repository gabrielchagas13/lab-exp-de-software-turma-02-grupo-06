import argparse
import csv
import statistics
import json

def load_rows(input_path: str) -> list[dict]:
    with open(input_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def to_number(value: str):
    if value in (None, ""):
        return None
    return float(value)

def analyze(rows: list[dict]):
    releases = []
    days_since_update = []
    
    categories_rq3 = {
        "0 releases": 0,
        "1-99 releases": 0,
        "100-999 releases": 0,
        "1000 releases (teto API)": 0
    }
    
    categories_rq4 = {
        "0 dias (hoje)": 0,
        "1-30 dias": 0,
        "31-365 dias": 0,
        "Mais de 365 dias": 0
    }
    
    for row in rows:
        r_val = to_number(row.get("total_releases"))
        d_val = to_number(row.get("days_since_update"))
        
        if r_val is not None:
            releases.append(r_val)
            if r_val == 0:
                categories_rq3["0 releases"] += 1
            elif r_val < 100:
                categories_rq3["1-99 releases"] += 1
            elif r_val < 1000:
                categories_rq3["100-999 releases"] += 1
            else:
                categories_rq3["1000 releases (teto API)"] += 1
                
        if d_val is not None:
            days_since_update.append(d_val)
            if d_val == 0:
                categories_rq4["0 dias (hoje)"] += 1
            elif d_val <= 30:
                categories_rq4["1-30 dias"] += 1
            elif d_val <= 365:
                categories_rq4["31-365 dias"] += 1
            else:
                categories_rq4["Mais de 365 dias"] += 1

    median_releases = statistics.median(releases) if releases else None
    median_days = statistics.median(days_since_update) if days_since_update else None
    
    return {
        "count_repos": len(rows),
        "RQ03_releases": {
            "median": median_releases,
            "categories": categories_rq3
        },
        "RQ04_days_since_update": {
            "median": median_days,
            "categories": categories_rq4
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Calcula medianas e contagens para RQ03 e RQ04")
    parser.add_argument("--input", default="data/repos_1000.csv", help="CSV de entrada com os dados dos repositorios")
    args = parser.parse_args()
    
    rows = load_rows(args.input)
    results = analyze(rows)
    
    print("=== RESULTADOS RQ03 (Total de Releases) ===")
    print(f"Mediana: {results['RQ03_releases']['median']}")
    print("Contagem por categorias:")
    for cat, count in results['RQ03_releases']['categories'].items():
        print(f"  - {cat}: {count} ({count/results['count_repos']:.1%})")
        
    print("\n=== RESULTADOS RQ04 (Tempo desde ultima atualizacao) ===")
    print(f"Mediana: {results['RQ04_days_since_update']['median']} dias")
    print("Contagem por categorias:")
    for cat, count in results['RQ04_days_since_update']['categories'].items():
        print(f"  - {cat}: {count} ({count/results['count_repos']:.1%})")

if __name__ == "__main__":
    main()
