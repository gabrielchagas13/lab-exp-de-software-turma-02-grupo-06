#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import argparse

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=cwd)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando: {' '.join(cmd)}")
        print(e.stderr)
        return None

def get_radon_raw(path):
    output = run_command([sys.executable, '-m', 'radon', 'raw', '-j', path])
    if not output: return 0
    try:
        data = json.loads(output)
        total_loc = 0
        for file, stats in data.items():
            if 'error' not in stats:
                total_loc += stats.get('loc', 0)
        return total_loc
    except json.JSONDecodeError:
        return 0

def get_radon_cc(path):
    output = run_command([sys.executable, '-m', 'radon', 'cc', '-j', path])
    if not output: return 0.0
    try:
        data = json.loads(output)
        blocks = []
        for file, file_blocks in data.items():
            if not isinstance(file_blocks, dict) or 'error' in file_blocks:
                continue
            blocks.extend(file_blocks)
            
        if not blocks: return 0.0
        
        total_complexity = sum(b.get('complexity', 1) for b in blocks)
        return total_complexity / len(blocks)
    except json.JSONDecodeError:
        return 0.0

def get_radon_mi(path):
    output = run_command([sys.executable, '-m', 'radon', 'mi', '-j', path])
    if not output: return 0.0
    try:
        data = json.loads(output)
        mis = []
        for file, stats in data.items():
            if isinstance(stats, dict) and 'mi' in stats:
                mis.append(stats['mi'])
        if not mis: return 0.0
        return sum(mis) / len(mis)
    except json.JSONDecodeError:
        return 0.0

def get_jscpd_duplication(path):
    # Usando npx para rodar o jscpd sem precisar instalação global prévia
    print("Executando jscpd para detectar duplicação (isso pode demorar um pouco)...")
    # jscpd não suporta saída fácil apenas com o percentual, precisamos do json
    out_dir = os.path.join(os.getcwd(), '.jscpd_temp')
    cmd = ['npx', '-y', 'jscpd', path, '--reporters', 'json', '--output', out_dir, '--silent']
    
    # Roda o comando
    subprocess.run(cmd, capture_output=True, text=True)
    
    report_file = os.path.join(out_dir, 'jscpd-report.json')
    if os.path.exists(report_file):
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
                duplication = data.get('statistics', {}).get('total', {}).get('percentage', 0.0)
            # Limpeza do diretório temporário
            import shutil
            shutil.rmtree(out_dir)
            return float(duplication)
        except Exception:
            pass
    return 0.0

def main():
    parser = argparse.ArgumentParser(description="Coleta métricas estáticas do código.")
    parser.add_argument("path", help="Caminho do arquivo ou diretório para análise")
    args = parser.parse_args()

    target_path = os.path.abspath(args.path)
    if not os.path.exists(target_path):
        print(f"Caminho não encontrado: {target_path}")
        sys.exit(1)

    print(f"Analisando métricas para: {target_path}")
    print("-" * 50)
    
    loc = get_radon_raw(target_path)
    print(f"LOC (Linhas de Código): {loc}")

    cc = get_radon_cc(target_path)
    print(f"Complexidade Ciclomática Média (McCabe): {cc:.2f}")

    mi = get_radon_mi(target_path)
    print(f"Índice de Manutenibilidade (MI): {mi:.2f}")

    dup = get_jscpd_duplication(target_path)
    print(f"Duplicação de Código: {dup:.2f}%")
    
    print("-" * 50)
    print("Concluído.")

if __name__ == "__main__":
    main()
