import sqlite3

from Gasto import Gasto
from Investiment import Investimento
import const

from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date

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
                    ),
                    parcela INTEGER DEFAULT 1 NOT NULL
                );
                """
            )

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

            # Cria tabela de investimentos
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS investimentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    tipo_ativo TEXT NOT NULL CHECK (
                        tipo_ativo IN {tuple(const.TIPOS_DE_ATIVOS)}
                    ),
                    tipo_taxa TEXT NOT NULL CHECK (
                        tipo_taxa IN {tuple(const.TIPOS_DE_TAXAS)}
                    ),
                    valor_inicial REAL NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_vencimento DATE,
                    percentual_contratado REAL DEFAULT 100.0 NOT NULL,
                    taxa_adicional_ipca REAL DEFAULT 0.0 NOT NULL,
                    valor_bruto REAL,
                    valor_liquido REAL,
                    lucro_liquido REAL
                );
                """
            )

            gastosDB.commit()

    # =========================================================================
    # MÉTODOS DE GASTOS
    # =========================================================================
    @staticmethod
    def insertGasto(gasto, parcelas="1"):
        parc = int(parcelas)
        data_base = date.fromisoformat(gasto.date)
        val_parc = gasto.price / parc
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            for i in range(parc):
                data_parcela = (data_base + relativedelta(months=i)).isoformat()
                cursor.execute(
                    """
                    INSERT INTO gastos (tipo_gasto, nome, dia, categoria, valor, metodo_pagamento, parcela)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (gasto.tipo, gasto.name, data_parcela, gasto.cat, val_parc, gasto.metodo, i+1),
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
                Order by dia DESC, id DESC
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

    # =========================================================================
    # MÉTODOS DE INVESTIMENTOS
    # =========================================================================
    @staticmethod
    def insertInvestimento(investimento):
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()
            cursor.execute(
                """
                INSERT INTO investimentos (nome, tipo_ativo, tipo_taxa, valor_inicial, data_inicio, data_vencimento, percentual_contratado, taxa_adicional_ipca, valor_bruto, valor_liquido, lucro_liquido)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (investimento.nome, investimento.tipo_ativo, investimento.tipo_taxa, investimento.valor_inicial, investimento.data_inicio.isoformat(), investimento.data_vencimento.isoformat() if investimento.data_vencimento else None, investimento.percentual_contratado, investimento.taxa_adicional_ipca, investimento._valor_bruto_cache, investimento.valor_liquido, investimento.lucro_liquido),
            )

            gastosDB.commit()

    @staticmethod
    def refreshInvestimentos():
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                SELECT * FROM investimentos
                """
            )

            investimentos = cursor.fetchall()

            for inv in investimentos:
                investimento = Investimento(
                    nome=inv[1],
                    tipo_ativo=inv[2],
                    tipo_taxa=inv[3],
                    valor_inicial=inv[4],
                    data_inicio=date.fromisoformat(inv[5]),
                    data_vencimento=date.fromisoformat(inv[6]) if inv[6] else None,
                    percentual_contratado=inv[7],
                    taxa_adicional_ipca=inv[8]
                )
                investimento.calcular_valor_bruto(forcar_recalculo=True)
                investimento.calcularLucro()

                cursor.execute(
                    """
                    UPDATE investimentos
                    SET valor_bruto = ?, valor_liquido = ?, lucro_liquido = ?
                    WHERE id = ?
                    """,
                    (investimento._valor_bruto_cache, investimento.valor_liquido, investimento.lucro_liquido, inv[0]),
                )

            gastosDB.commit()

    @staticmethod
    def getAllInvestimentos():
        with sqlite3.connect(DataBase.nome) as gastosDB:
            cursor = gastosDB.cursor()

            cursor.execute(
                """
                SELECT nome, data_inicio, data_vencimento, valor_inicial, ROUND(valor_liquido, 2) as valor_liquido, ROUND(lucro_liquido, 2) as lucro_liquido FROM investimentos
                Order by data_inicio DESC, id DESC
                """
            )

            gastosDB.commit()

            nomes_colunas = [coluna[0] for coluna in cursor.description]
            return cursor.fetchall(), nomes_colunas
    # =========================================================================
    # MÉTODOS DE SALDO
    # =========================================================================
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

    # =========================================================================
    # MÉTODOS AUXILIARES
    # =========================================================================
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
    def insertCol(table, colName, dtype, default=None):
        with sqlite3.connect(DataBase.nome) as conn:
            cursor = conn.cursor()

            try:
                if default is not None:
                    cursor.execute(
                        f"""
                        ALTER TABLE {table}
                        ADD {colName} {dtype} DEFAULT {default}
                        """
                        )
                else:
                    cursor.execute(
                        f"""
                        ALTER TABLE {table}
                        ADD {colName} {dtype}
                        """
                        )
            except Exception as e:
                print("Failed to add new column")
                print(e)

""" Testes manuais """
# db = DataBase()
# db.destroyTable("investimentos")
# db.insertCol("gastos", "parcela", "INTEGER", 1)
# DataBase.transposeGastos()
#DataBase.deleteGasto(24)
#DataBase.consultaManual("SELECT sql FROM sqlite_master  WHERE type = 'table' AND name = 'nome_da_tabela';")