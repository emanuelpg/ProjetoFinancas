import sqlite3
from Gasto import Gasto

class DataBase:
    nome = "financas.db"
    def __init__(self):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            # Cria tabela de gastos
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    dia DATE NOT NULL,
                    valor REAL NOT NULL,
                    tipo_gasto TEXT NOT NULL CHECK (
                        tipo_gasto IN ("Gasto Fixo", "Gasto Não Fixo", "Income", "Investimento")
                    ),
                    categoria TEXT NOT NULL CHECK (
                        categoria IN ('Doce', 'Fruta', 'Comida Pronta', 'Comida para Fazer', 'Saúde', 'Higiene', 'Planejado', 'Transporte', 'Reserva', 
                        'caixinha', 'Renda Fixa', 'Assinatura', 'Conta', 'outros')
                    ),
                    metodo_pagamento TEXT NOT NULL CHECK (
                        metodo_pagamento IN ('Crédito', 'Débito')
                    )
                );
                """
            )
            gastosDB.commit()

    @staticmethod
    def insertGasto(gasto):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                INSERT INTO gastos (tipo_gasto, nome, dia, categoria, valor, metodo_pagamento)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (gasto.tipo, gasto.name, gasto.date, gasto.cat, gasto.price, gasto.metodo),
            )

            gastosDB.commit()

    @staticmethod
    def showGastos():
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                SELECT * FROM gastos
                """
            )

            gastosDB.commit()
            print(cursor.fetchall())

    @staticmethod
    def getAllGastos():
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                SELECT * FROM gastos
                Order by dia DESC
                """
            )

            gastosDB.commit()
            return cursor.fetchall()

    @staticmethod
    def deleteGasto(id):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                DELETE FROM gastos WHERE id = ?
                """,
                (str(id)),
            )

            gastosDB.commit()

    @staticmethod
    def clearGastos():
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            cursor.execute(
                """
                DELETE FROM gastos
                """
            )       
            gastosDB.commit()    

    @staticmethod
    def destroyTable(table):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            cursor.execute(
                f"""
                DROP TABLE IF EXISTS {table}
                """
            ) 
            gastosDB.commit() 

    @staticmethod
    def consultaManual(query):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            cursor.execute(query) 
            gastosDB.commit() 
            nomes_colunas = [coluna[0] for coluna in cursor.description]
            return cursor.fetchall(), nomes_colunas

    

            
