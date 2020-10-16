from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key= "Inventorymanagement"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventorymanagement.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]= False

db = SQLAlchemy(app)

class Products(db.Model):
    product_id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)   

    def __repr__(self):
        return self.product_name

class Locations(db.Model):
    location_id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100),nullable=False)

    def __repr__(self):
        return self.location_name

class Movements(db.Model):
    movement_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location_from = db.Column(db.String(100))
    location_to = db.Column(db.String(100))
    product_name = db.Column(db.String(50), nullable=False)
    pro_id = db.Column(db.Integer, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.movement_id


@app.route("/")
@app.route("/index")
def home():
    return render_template("index.html")

@app.route("/products" ,methods = ['GET', 'POST'])
def product():
    if request.method == 'POST':
        if 'product_name' in request.form:
            product_name = request.form['product_name']
            if Products.query.filter_by(product_name = product_name).first():
                flash(f" Product '{product_name}' Already Exists!",'danger')
            else:
                new = Products(product_name = product_name)
                product = Products.query.filter_by(product_name = product_name).first()
                db.session.add(new)
                flash(f" Your Product '{product_name}' is Saved!",'success')

        
        if 'edit_product' in request.form:
            product_id = request.form['edit_product']
            exist = Products.query.filter_by(product_id=product_id).first()
            product_name = request.form["product_edit"]
            product_movements = Movements.query.filter_by(product_name= exist.product_name).all()
            if product_movements:
                for item in product_movements:
                    item.product_name = product_name
            exist.product_name = product_name
            flash(f"Product is updated Sucessfully!", "success")
        
        db.session.commit()
        return redirect(url_for('product'))
    
    data = get_all_items()
    return render_template("product.html", products = data)

@app.route("/location" ,methods = ["GET", "POST"])
def location():
    
    if request.method == 'POST':
        if 'location_name' in request.form:
            location_name = request.form['location_name']
            if Locations.query.filter_by(location_name = location_name).first():
                flash(f" Location '{location_name}' Already Exists!",'danger')
            else:
                newloc = Locations(location_name = location_name)
                location = Locations.query.filter_by(location_name = location_name).first()
                db.session.add(newloc)
                flash(f" Your Location '{location_name}' is Saved!",'success')

        if 'edit_location' in request.form:
            location_id = request.form['edit_location']
            exist = Locations.query.filter_by(location_id=location_id).first()
            location_name = request.form["location_edit"]
            from_movements = Movements.query.filter_by(location_from=exist.location_name).all()
            if from_movements:
                for item in from_movements:
                    item.location_from = location_name
            to_movements = Movements.query.filter_by(location_to=exist.location_name).all()
            if to_movements:
                for item in to_movements:
                    item.to_movements = location_name
            exist.location_name = location_name
            flash(f"Product is updated Sucessfully!", "success")
        
        db.session.commit()
        return redirect(url_for('location'))

    data = get_location()
    return render_template("location.html", locations = data)

@app.route("/movement" ,methods = ["GET", "POST"])
def movement():
    if request.method == 'POST':
        if 'edit_movement' in request.form:
            edit_valid = True
            movement_id = request.form['edit_movement']
            new_qty = int(request.form["product_quantity"])
        
            movement = Movements.query.filter_by(movement_id=movement_id).first()
            movement_product = movement.product_name
            movement_from = movement.location_to
            movement_to = movement.location_from

            import_move = Movements.query.filter_by(product_name = movement_product).filter_by(location_to= movement_to).count()
            export_move = Movements.query.filter_by(product_name = movement_product).filter_by(location_from = movement_from).count()
            if import_move > 0:
                import_items = get_importing(movement_product,movement_to)
                if import_items:
                    import_quantity = 0
                    for items in import_items:
                        import_quantity += items.product_quantity
                    if import_quantity < int(new_qty):
                            edit_valid = False
                            flash(f"Quantity is not available, Cannot be Updated!", "danger")
            if export_move > 0:
                export_items = get_exporting(movement_product,movement_from)
                if export_items:
                    export_quantity = 0
                    for items in export_items:
                        export_quantity += items.product_quantity
                    if export_quantity > int(new_qty):
                            edit_valid = False
                            flash(f"Exceeds Quantity, Cannot be Updated!", "danger")
            if edit_valid:
                movement.product_quantity = new_qty
                db.session.commit()
                flash(f"Movement Updated Successfully!", "success")

        
        if 'product_id' in request.form:
            valid = True
            product_name = None
            product_quantity = None
            location_from = request.form['location_from']
            location_to = request.form['location_to']
            
            if location_from != "Select Location From" or location_to != "Select Location To":
                if location_from == location_to:
                    flash(f"Location cannot be same","danger")
                    valid = False
                
            else:
                flash(f"Location not Selected, Select atleast Once!","danger")
                valid = False

            if request.form['product_name'] == 'Select Product Name':
                flash(f"Please Select Product name!","danger")
                valid = False

            else:
                product_name = request.form['product_name']
                if request.form["product_quantity"] != None :
                    if int(request.form["product_quantity"]) > 0:
                        product_quantity = request.form["product_quantity"]
                    if location_from != "Select Location From":
                        total_items = total_count(product_name,location_from)
                        if total_items == 0:
                            flash(f"Quantity Stock not available at { location_from }" ,"danger")
                            valid = False
                        elif int(product_quantity) > total_items:
                            flash(f"Quantity cannot be greater than available!" ,"danger")
                            valid = False
                        elif int(product_quantity) <= total_items:
                            valid = True


            if valid:
                location_from = request.form['location_from']
                location_to = request.form['location_to']
                product_id = request.form['product_id']
                product_name = request.form['product_name']
                product_quantity = request.form['product_quantity']
                newmove = Movements(location_from= location_from, location_to=location_to,product_name=product_name,product_quantity= product_quantity)
                db.session.add(newmove)
                flash(f" Your Product Movement '{product_name}' is Saved!",'success')
                db.session.commit()
            return redirect(url_for('movement'))

    movements = Movements.query.all()
    return render_template("movements.html", movements= movements, products = Products.query.all(),locations = Locations.query.all())  


def total_count(product, location):
    importing = 0
    exporting = 0
    importing_items = get_importing(product,location)
    if importing_items:
        for items in importing_items:
            importing += items.product_quantity
    exporting_items = get_exporting(product,location)
    if exporting_items:
        for items in exporting_items:
            exporting += items.product_quantity
    total = importing - exporting
    return total


def get_importing(product,location):
    importing = Movements.query.filter_by(product_name= product).filter_by(location_to=location).all()
    return importing


def get_exporting(product,location):
    exporting = Movements.query.filter_by(product_name= product).filter_by(location_from=location).all()
    return exporting

def overallinfo(product,location):
    overallinfo = []
    products = Products.query.all()
    locations =Locations.query.all()
    for location in locations:
        for product in products:
            info = {}
            pname = product.product_name
            lname = location.location_name
            total = total_count(pname, lname)
            info['product'] = pname
            info['location'] = lname
            if total == 0:
                continue
            else:
                info['available_quantity'] = total
            overallinfo.append(info)
    return overallinfo


@app.route("/overview")
def overview(prod=[],loc=[]):
    if 'product' in request.args:
        prod = request.args.getlist('product')
    if 'location' in request.args:
        loc = request.args.getlist('location')
    info = overallinfo(prod,loc)
    
    products = Products.query.all()
    locations = Locations.query.all()
    
    return render_template("overview.html",overallinfo=info, products = products, locations = locations)


def get_all_items():    
    products = Products.query.all()
    locations = Locations.query.all()
    prod_data = []
    for product in products:
        importing = 0
        exporting = 0
        data = {}
        for location in locations:
            import_items = get_importing(product.product_name, location.location_name)
            if import_items:
                for item in import_items:
                    importing += item.product_quantity
            export_items = get_exporting(product.product_name, location.location_name)
            if export_items:
                for item in export_items:
                    exporting += item.product_quantity
        total = importing - exporting
        data['id'] = product.product_id
        data['product_name'] = product.product_name
        data['product_quantity'] = total
        prod_data.append(data)

    return prod_data


def get_location():
    locations = Locations.query.all()
    products = Products.query.all()
    loc_data = []
    for location in locations:
        data = {}
        prod_data = []
        for product in products:
            total = total_count(product.product_name, location.location_name)
            if total > 0:
                prod_data.append(product.product_name)

        prod_list = ', '.join(prod_data)
        data['id'] = location.location_id
        data['location_name'] = location.location_name
        data['product_list'] = prod_list
        loc_data.append(data)
    return loc_data






@app.route("/delete")
def delete():
    type = request.args.get('type')
    if type == 'product':
        product_id = request.args.get('product_id')
        product = Products.query.filter_by(product_id=product_id).delete()
        db.session.commit()
        flash(f'Your product  has been deleted!', 'success')
        return redirect(url_for('product'))
        return render_template('product.html',title = 'Products')
    elif type == 'location':
        location_id = request.args.get('location_id')
        location = Locations.query.filter_by(location_id = location_id).delete()
        db.session.commit()
        flash(f'Your location  has been deleted!', 'success')
        return redirect(url_for('location'))
        return render_template('location.html',title = 'Locations')
    if type == 'movement':
        movement_id = request.args.get('movement_id')
        movement = Movements.query.filter_by(movement_id=movement_id).delete()
        db.session.commit()
        flash(f'Your product  has been deleted!', 'success')
        return redirect(url_for('movement'))
        return render_template('movements.html',title = 'Movements')


if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)