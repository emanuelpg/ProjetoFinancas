import sqlite3
from Gasto import Gasto
import const
from datetime import datetime

class DataBase:
    nome = "financas.db"
    def __init__(self):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            # Consulta o catálogo do SQLite
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='saldo';
            """)

            resultado = cursor.fetchone()

            if resultado:
                self.first = 0
                try:
                    DataBase.saldo = DataBase.consultaSaldo()
                except:
                    self.first = 1
                    DataBase.saldo = 0
            else:
                self.first = 1
                DataBase.saldo = 0

            # Cria tabela de gastos
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS gastos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    dia DATE NOT NULL,
                    valor REAL NOT NULL,
                    tipo_gasto TEXT NOT NULL CHECK (
                        tipo_gasto IN {tuple(const.TIPOS_DE_GASTO)}
                    ),
                    categoria TEXT NOT NULL CHECK (
                        categoria IN {tuple(const.CATEGORIAS)}
                    ),
                    metodo_pagamento TEXT NOT NULL CHECK (
                        metodo_pagamento IN {tuple(const.METODOS_PAGAMENTO)}
                    )
                );
                """
            )
            # cursor.execute(
            #     f"""
            #     ALTER TABLE gastos ADD CONSTRAINT chk_categoria CHECK (
            #         categoria IN {tuple(const.CATEGORIAS)}
            #     );
            #     """
            # )
            # Cria tabela de saldos
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS saldo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    saldo_total REAL,
                    dia DATE NOT NULL
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

            if gasto.tipo in ["Gasto Fixo", "Gasto Não Fixo"]:
                DataBase.saldo = DataBase.atualizaSaldo(DataBase.saldo-float(gasto.price))
            elif gasto.tipo == "Entrada":
                DataBase.saldo = DataBase.atualizaSaldo(DataBase.saldo+float(gasto.price))

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
                f"""
                DELETE FROM gastos WHERE id = {str(id)}
                """
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

    @staticmethod
    def consultaSaldo(mes=None):
        if mes is None:
            return DataBase.consultaManual("select saldo_total from saldo Order by dia DESC, id DESC")[0][0][0]
        else:
            query = f"""
            select
            COALESCE(i.entradas, 0) - COALESCE(o.saidas, 0) AS saldo,
            COALESCE(i.entradas, 0) AS entradas,
            COALESCE(o.saidas, 0) AS saidas from 
            (
                select sum(valor) as saidas, strftime('%Y-%m', dia) AS mes 
                from gastos
                where mes = '{mes}' AND tipo_gasto in ('Gasto Fixo', 'Gasto Não Fixo')
            ) as o,
            (
                select sum(valor) as entradas, strftime('%Y-%m', dia) AS mes 
                from gastos
                where mes = '{mes}' AND tipo_gasto in ('Entrada')
            ) as i;
            """
            saldo, entrada, saida = DataBase.consultaManual(query)[0][0]
            return saldo, saida, entrada

    @staticmethod
    def atualizaSaldo(new_value, day=None):
        if day is None:
            day = datetime.today().strftime('%Y-%m-%d')
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            cursor.execute(f"INSERT INTO saldo (saldo_total, dia) VALUES (?, ?)", (new_value, day)) 
            gastosDB.commit() 

            return new_value
        return None

    @staticmethod
    def transposeGastos():
        with sqlite3.connect(DataBase.nome) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = OFF;")
            cursor.execute("BEGIN TRANSACTION;")

            try:
                cursor.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS nova (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        dia DATE NOT NULL,
                        valor REAL NOT NULL,
                        tipo_gasto TEXT NOT NULL CHECK (
                            tipo_gasto IN {tuple(const.TIPOS_DE_GASTO)}
                        ),
                        categoria TEXT NOT NULL CHECK (
                            categoria IN {tuple(const.CATEGORIAS)}
                        ),
                        metodo_pagamento TEXT NOT NULL CHECK (
                            metodo_pagamento IN {tuple(const.METODOS_PAGAMENTO)}
                        )
                    );
                    """
                )

                cursor.execute("""
                    INSERT INTO nova (id, nome, dia, valor, tipo_gasto, categoria, metodo_pagamento)
                    SELECT id, nome, dia, valor, tipo_gasto, categoria, metodo_pagamento FROM gastos;
                """)

                cursor.execute("DROP TABLE gastos;")

                cursor.execute("ALTER TABLE nova RENAME TO gastos;")

                conn.commit()
                print("Column constraint updated successfully!")

            except Exception as e:
                conn.rollback()
                print(f"Failed to update constraint, rolled back: {e}")

            finally:
                # 8. Re-enable foreign keys
                cursor.execute("PRAGMA foreign_keys = ON;")

#db = DataBase()
# DataBase.transposeGastos()
#DataBase.deleteGasto(24)
#DataBase.consultaManual("SELECT sql FROM sqlite_master  WHERE type = 'table' AND name = 'nome_da_tabela';")