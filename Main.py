from Application import App

if __name__ == "__main__":
    app = App()
    app.mainloop()


"""
select distinct 
    strftime('%Y-%m', dia) AS mes
FROM gastos

select
    strftime('%Y-%m', dia) AS mes,
    SUM(valor) as gasto_total,
    tipo_gasto
FROM gastos
where mes = '2026-09' 
GROUP BY tipo_gasto, mes
ORDER BY mes DESC;
"""

""