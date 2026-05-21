from flask import Flask, render_template, request, redirect, url_for, flash
import oracledb
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'proiect_bd_secret_key'

# local connection configuration
DB_CONFIG = {
    "user": "user_app",
    "password": "bazededate",
    "dsn": "localhost:1521/xe"
}


def get_db_connection():
    return oracledb.connect(user=DB_CONFIG["user"], password=DB_CONFIG["password"], dsn=DB_CONFIG["dsn"])


@app.context_processor
def inject_global_vars():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return dict(all_tables=tables)
    except:
        return dict(all_tables=[])


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/table/<name>')
def show_table(name):
    sort_col = request.args.get('sort', None)
    direction = request.args.get('dir', 'ASC')
    if direction not in ['ASC', 'DESC']:
        direction = 'ASC'

    is_query = False
    if name.upper() in ['V_STATISTICI_VANZARI', 'CERERE_C', 'ANALIZA_D']:
        is_query = True

    is_view = False
    if name.upper() in ['V_PRODUS_PRODUCATOR', 'V_STATISTICI_VANZARI']:
        is_view = True

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f'SELECT * FROM "{name.upper()}"'
        if sort_col:
            query += f' ORDER BY "{sort_col}" {direction}'
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        conn.close()

        return render_template('table.html',
                               table_name=name.upper(),
                               data=data,
                               columns=columns,
                               current_sort=sort_col,
                               current_dir=direction,
                               is_query=is_query,
                               is_view=is_view)
    except Exception as e:
        flash(f"Eroare: {e}", "danger")
        return redirect(url_for('index'))


@app.route('/edit/<table_name>/<id>', methods=['GET', 'POST'])
def edit_item(table_name, id):
    conn = get_db_connection()
    cursor = conn.cursor()

    display_table = table_name.upper()
    target_table = display_table

    if display_table == 'V_PRODUS_PRODUCATOR':
        target_table = 'PRODUS'

    cursor.execute(f'SELECT * FROM "{target_table}" WHERE ROWNUM = 1')
    base_columns = [col[0] for col in cursor.description]
    column_types = {col[0]: col[1] for col in cursor.description}
    pk_col = base_columns[0]

    if request.method == 'POST':
        update_parts = []
        params = {}
        error_found = False

        for col in base_columns:
            val = request.form.get(col)
            if val is not None:
                val = val.strip()
                if val == "":
                    val = None

            if val is not None or col != pk_col:
                is_date_type = (column_types[col] == oracledb.DB_TYPE_DATE or
                                "DATE" in str(column_types[col]).upper())

                if is_date_type and val is not None:
                    date_valid = False
                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                        date_valid = True
                        update_parts.append(f'"{col}" = TO_DATE(:{col}, \'YYYY-MM-DD\')')
                    except ValueError:
                        pass

                    if not date_valid:
                        try:
                            datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                            date_valid = True
                            update_parts.append(f'"{col}" = TO_DATE(:{col}, \'YYYY-MM-DD HH24:MI:SS\')')
                        except ValueError:
                            pass

                    if not date_valid:
                        flash(
                            f"Eroare la câmpul '{col}': Formatul datei este incorect! Folosește 'AAAA-LL-ZZ' (ex: 2023-11-25) sau 'AAAA-LL-ZZ HH:MM:SS' (ex: 2023-11-25 21:10:50).",
                            "danger")
                        error_found = True
                        break
                else:
                    update_parts.append(f'"{col}" = :{col}')

                params[col] = val

        if error_found:
            cursor.execute(f'SELECT * FROM "{display_table}" WHERE "{pk_col}" = :1', [id])
            row = cursor.fetchone()
            cursor.execute(f'SELECT * FROM "{display_table}" WHERE ROWNUM = 1')
            view_columns = [col[0] for col in cursor.description]
            conn.close()
            record_data = dict(zip(view_columns, row)) if row else {}
            return render_template('edit.html', table_name=display_table, columns=view_columns, record_data=record_data)

        sql = f'UPDATE "{target_table}" SET {", ".join(update_parts)} WHERE "{pk_col}" = :pk_val'
        params['pk_val'] = id
        try:
            cursor.execute(sql, params)
            conn.commit()
            flash(f"Succes: Înregistrarea a fost actualizată în {target_table}.", "success")
            conn.close()
            return redirect(url_for('show_table', name=table_name))
        except Exception as e:
            flash(f"Eroare SQL la salvare: {e}", "danger")

    cursor.execute(f'SELECT * FROM "{display_table}" WHERE "{pk_col}" = :1', [id])
    row = cursor.fetchone()

    cursor.execute(f'SELECT * FROM "{display_table}" WHERE ROWNUM = 1')
    view_columns = [col[0] for col in cursor.description]
    conn.close()

    if not row:
        return redirect(url_for('index'))

    record_data = dict(zip(view_columns, row))
    return render_template('edit.html', table_name=display_table, columns=view_columns, record_data=record_data)

@app.route('/delete/<table_name>/<id>')
def delete_item(table_name, id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        target_table = table_name.upper()
        if target_table == 'V_PRODUS_PRODUCATOR':
            target_table = 'PRODUS'

        cursor.execute(f'SELECT * FROM "{target_table}" WHERE ROWNUM = 1')
        pk_col = cursor.description[0][0]

        cursor.execute(f'DELETE FROM "{target_table}" WHERE "{pk_col}" = :1', [id])
        conn.commit()
        conn.close()
        flash(f"Succes: Înregistrarea a fost ștearsă din {target_table}.", "warning")
    except Exception as e:
        flash(f"Eroare la ștergere: {e}", "danger")
    return redirect(url_for('show_table', name=table_name))


@app.route('/add/<table_name>', methods=['GET', 'POST'])
def add_item(table_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    display_table = table_name.upper()
    target_table = display_table

    cursor.execute(f'SELECT * FROM "{target_table}" WHERE ROWNUM = 1')
    base_columns = [col[0] for col in cursor.description]
    column_types = {col[0]: col[1] for col in cursor.description}

    cursor.execute("""
        SELECT column_name 
        FROM user_tab_cols 
        WHERE table_name = :table_name AND nullable = 'N'
    """, {"table_name": target_table})
    not_null_columns = {row[0] for row in cursor.fetchall()}

    display_columns = []
    for column in base_columns:
        if column in not_null_columns:
            display_columns.append(column + "*")
        else:
            display_columns.append(column)

    if request.method == 'POST':
        insert_parts = []
        columns = []
        params = {}
        error_found = False

        for col in base_columns:
            val = request.form.get(col)
            if val is not None:
                val = val.strip()

            if (val is None or val == "") and col in not_null_columns:
                flash(f"Eroare: Câmpul '{col}' este obligatoriu!", "danger")
                error_found = True
                break

            if val == "":
                val = None

            if val is not None or col not in not_null_columns:
                columns.append(f'"{col}"')

                is_date_type = (column_types[col] == oracledb.DB_TYPE_DATE or
                                "DATE" in str(column_types[col]).upper())

                if is_date_type and val is not None:
                    date_valid = False

                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                        date_valid = True
                        insert_parts.append(f"TO_DATE(:{col}, 'YYYY-MM-DD')")
                    except ValueError:
                        pass

                    if not date_valid:
                        try:
                            datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
                            date_valid = True
                            insert_parts.append(f"TO_DATE(:{col}, 'YYYY-MM-DD HH24:MI:SS')")
                        except ValueError:
                            pass

                    if not date_valid:
                        flash(
                            f"Eroare la câmpul '{col}': Formatul datei este incorect! Folosește 'AAAA-LL-ZZ' (ex: 2023-11-25) sau 'AAAA-LL-ZZ HH:MM:SS' (ex: 2023-11-25 21:10:50).",
                            "danger")
                        error_found = True
                        break
                else:
                    insert_parts.append(f':{col}')

                params[col] = val

        if error_found:
            conn.close()
            return render_template('insert.html', table_name=display_table, columns=display_columns, saved_data=request.form)

        sql = f'INSERT INTO "{target_table}" ({", ".join(columns)}) VALUES ({", ".join(insert_parts)})'
        try:
            cursor.execute(sql, params)
            conn.commit()
            flash(f"Succes: Înregistrarea a fost introdusă în {target_table}.", "success")
            conn.close()
            return redirect(url_for('show_table', name=table_name))
        except Exception as e:
            flash(f"Eroare SQL la salvare: {e}", "danger")

    conn.close()
    return render_template('insert.html', table_name=display_table, columns=display_columns, saved_data=None)

@app.route('/query-c')
def query_c():
    sql = """
    select u.nume, u.prenume, p.nume PRODUS, count(p.produs_id) as "NUMAR PRODUSE"
    from utilizator u join comanda c on (u.utilizator_id = c.utilizator_id)
                    join elemente_comanda e on (e.comanda_id = c.comanda_id)
                    join produs p on (p.produs_id = e.produs_id)
    where frecventa_minima >= 10 and pret >= 500
    group by u.utilizator_id, u.nume, u.prenume, p.nume
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [col[0] for col in cursor.description]
    data = cursor.fetchall()
    conn.close()
    return render_template('table.html', table_name="Raport clienți", data=data, columns=columns, is_query=True)


@app.route('/query-d')
def query_d():
    sql = """
    select a.nume as "Nume producator", round(avg(b.pret), 2) as "Pret mediu produse", count(b.produs_id) as "Numar produse"
    from producator a join produs b on (a.producator_id = b.producator_id)
    group by a.producator_id, a.nume
    having avg(b.pret) >= 300 and count(b.produs_id) >= 2
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql)
    columns = [col[0] for col in cursor.description]
    data = cursor.fetchall()
    conn.close()
    return render_template('table.html', table_name="Analiză producători", data=data, columns=columns, is_query=True)


if __name__ == '__main__':
    app.run(debug=True)