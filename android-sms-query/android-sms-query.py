body_ct = [
    "emprestimo",
    "recarga",
    "estimado",
    "transfer",
    "refer",
    "assegurar",
    "transacção",
    "taxas",
    "pagar",
    "efectuado",
    "pedido",
    "carteira",
    "sucesso",
    "limite",
    "aoa",
    "pagamento",
    "kz",
    "recebe",
    "depósito",
    "express",
    "débito",
    "entidade",
    "dinheiro",
    "saldo",
    "crédito",
    "creditado",
    "enviado",
    "reembolso",
]

addr_ct = ["banco", "money", "cash", "uanza", "bai", "bfa"]

body_exct = ["activacao", "válido", "verificação"]

# (lower(body) like '%key% or lower.....)  or (lower(address) like '%key%'  or lower......) and (lower(body) not like '%key%' or lower.....)

selection = "("
selection += " or ".join([f"body like '%{keyword}%'" for keyword in body_ct])
selection += ") or ("
selection += "("
selection += " or ".join([f"address like '%{keyword}%'" for keyword in addr_ct])
selection += ") and ("
selection += " or ".join([f"body not like '%{keyword}%'" for keyword in body_exct])
selection += "))"

print(selection)
