import sys
import os
from google.appengine.ext import ndb
from flask import Flask, flash, render_template, request, Response, jsonify, session
import json


class JsonData(ndb.Model):
    """Google Datastore Entity Model.

    Data entity representing rows from NCHS - Leading Causes of Death: United States dataset:
    https://catalog.data.gov/dataset/age-adjusted-death-rates-for-the-top-10-leading-causes-of-death-united-states-2013

    Attributes:
        json_data: JSON object from 'us-death.json'.
        id: String computed property (year + cause + region), should be unique for deletion to work properly.
        deaths, deathRate: Computed values parsed from JSON.
        yearValue, causeValue, regionValue: String properties parsed from JSON.
        date: Date nbb property set on put().
    """
    json_data = ndb.JsonProperty()
    id = ndb.ComputedProperty(lambda self: str(self.json_data['Year'])
                                           + self.json_data['CauseName']
                                           + self.json_data['State'])
    deaths = ndb.ComputedProperty(lambda self: self.json_data['Deaths'])
    deathRate = ndb.ComputedProperty(lambda self: self.json_data['AgeAdjustedDeathRate'])
    yearValue = ndb.StringProperty()
    causeValue = ndb.StringProperty()
    regionValue = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)


app = Flask(__name__)
app.secret_key = os.urandom(12)
SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, 'static', 'us-death.json')
data = json.load(open(json_url))
print type(data)
dataQuery = JsonData.query()
orders = [(-JsonData.causeValue).reversed(),
          (-JsonData.yearValue).reversed(),
          (-JsonData.regionValue).reversed()]
filters = [{}]
filters[0] = {}
orderedQuery = [dataQuery.order(*orders)]
order = orderedQuery[0].orders
reversed_order = order.reversed()
revOrderedQuery = [JsonData.query().order(reversed_order)]
causeQuery = JsonData.query(projection=[JsonData.causeValue],
                            distinct=True).order(JsonData.causeValue).fetch()
regionQuery = JsonData.query(projection=[JsonData.regionValue],
                             distinct=True).order(JsonData.regionValue).fetch()
cursorObject = [None, None]
entries = [None]
more = [True]
r_more = [False]


# print dataQuery.get()
def custom_query(**kwargs):
    """Query Filter Builder.

    Args:
        kwargs: Dictionary of keywords to parse into ndb query constructor.

    Returns:
        qry: Datastore query of JsonData entities matching filters in kwargs
    """
    qry = JsonData.query(*(getattr(JsonData, k)==v for (k,v) in kwargs.items()))
    return qry


#
#
@app.route('/')
def home():
    """Index Template Output.

    Called on original http request. Initializes session objects for client interaction.

    Returns:
        render_template: index.html page to client.
    """
    # if not session.get('logged_in'):
    #     return render_template('login.html')
    cursorObject[0] = cursorObject[1]
    del orders[:]
    orders.append((-JsonData.causeValue).reversed())
    orders.append((-JsonData.yearValue).reversed())
    orders.append((-JsonData.regionValue).reversed())
    print(orders)
    orderedQuery[0] = JsonData.query().order(*orders)
    entries[0], cursorObject[0], more[0] = orderedQuery[0].fetch_page(50)
    print more[0]
    local_order = orderedQuery[0].orders
    local_reversed_order = local_order.reversed()
    revOrderedQuery[0] = JsonData.query().order(local_reversed_order)
    return render_template('index.html')


# @app.route('/login', methods=['POST'])
# def login():
#     login_info = request.get_json()
#     if login_info['password'] == 'password' and login_info['username'] == 'admin':
#         print login_info
#         session['logged_in'] = True
#     else:
#         print('wrong password!')
#     return home()


@app.route('/filter', methods=['POST'])
def filter_datastore():
    """Filter Datastore.

    Receives JSON from client that is parsed to construct a filtered query.

    Returns:
        JSON success message
    """
    def get_filters(filter_data):
        """Get Filters.

        Args:
            filter_data: List of strings representing query filters.

        Returns:
            datastore_filters: List of ndb properties for query building.
        """
        if len(filter_data) == 0:
            return filter_data
        datastore_filters = {}
        for key in filter_data:
            if filter_data[key] == "" or filter_data[key] is None:
                continue
            if key == 'CauseName':
                datastore_filters['causeValue'] = filter_data[key]
            elif key == 'State':
                datastore_filters['regionValue'] = filter_data[key]
            elif key == 'Year':
                datastore_filters['yearValue'] = filter_data[key]
            elif key == 'Deaths':
                datastore_filters['deaths'] = filter_data[key]
            elif key == 'AgeAdjustedDeathRate':
                datastore_filters['deathRate'] = filter_data[key]
        return datastore_filters
    filter_options = request.get_json()
    print filter_options
    filters[0] = get_filters(filter_options)
    orderedQuery[0] = custom_query(**filters[0]).order(*orders)
    return jsonify(status="success", data=data)


@app.route('/sort', methods=['POST'])
def order():
    """Order Datastore.

        Receives JSON from client that is parsed to construct a ordered query.

        Returns:
            JSON success message.
    """
    def get_orders(order):
        """Get Order.

            Args:
                order: String representing query order.

            Returns:
                (bool-if-reversed, -JsonData.Property): Tuple of boolean, to determine whether or not to reverse the
                order after, and an ndb query order object, negated to enforce typing.
        """
        if order['order'] == 'CauseName':
            if order['direction'] == 'asc':
                return [True, -JsonData.causeValue]
            else:
                return [False, -JsonData.causeValue]
        elif order['order'] == 'State':
            if order['direction'] == 'asc':
                return [True, -JsonData.regionValue]
            else:
                return [False, -JsonData.regionValue]
        elif order['order'] == 'Year':
            if order['direction'] == 'asc':
                return [True, -JsonData.yearValue]
            else:
                return [False, -JsonData.yearValue]
        elif order['order'] == 'Deaths':
            if order['direction'] == 'asc':
                return [True, -JsonData.deaths]
            else:
                return [False, -JsonData.deaths]
        elif order['order'] == 'AgeAdjustedDeathRate':
            if order['direction'] == 'asc':
                return [True, -JsonData.deathRate]
            else:
                return [False, -JsonData.deathRate]
    sort_options = request.get_json()
    sort = get_orders(sort_options)
    if sort[0]:
        sort[1] = sort[1].reversed()
    if sort[1] in orders:
        del orders[:]  # Change this to allow multiple order arguments. Beware of index explosion.
        orders.insert(0, sort[1])
    elif sort[1].reversed() in orders:
        del orders[:]  # Change this to allow multiple order arguments. Beware of index explosion.
        orders.insert(0, sort[1])
    else:
        del orders[:]  # Change this to allow multiple order arguments. Beware of index explosion.
        orders.insert(0, sort[1])
    orderedQuery[0] = custom_query(**filters[0]).order(*orders)
    local_order = orderedQuery[0].orders
    local_reversed_order = local_order.reversed()
    revOrderedQuery[0] = JsonData.query().order(local_reversed_order)
    return jsonify(status="success", data=data)


@app.route('/get-sort', methods=['GET'])
def return_sort():
    """Return Sorted Query Results.

        Returns query results ordered by most recent order and filter to client for display. Also sends next/prev
        booleans for navigation buttons.

        Returns:
            JSON Response containing new query results and navigation button bools.
    """
    json_array = []
    entries[0], cursorObject[0], more[0] = orderedQuery[0].fetch_page(50)
    return_data = {"records": json_array, "next": more[0], "prev": False}
    for i in entries[0]:
        json_array.append(i.json_data)
    return Response(json.dumps(return_data), mimetype='application/json')


@app.route('/data', methods=['GET'])
def get_data():
    """Get Initial Query Results.

        Returns query results ordered by original order and filter to client for display. Also sends next/prev
        booleans for navigation buttons and unique values of causes and regions for select boxes. Called once on
        client load i.e. after home().

        Returns:
            JSON Response containing new query results, navigation button bools.
    """
    json_array = []
    causes = []
    regions = []
    return_data = {"records": json_array, "causes": causes, "regions": regions, "next": more[0], "prev": False}
    for i in causeQuery:
        causes.append(i.causeValue)
    for i in regionQuery:
        regions.append(i.regionValue)
    for i in entries[0]:
        json_array.append(i.json_data)
    return Response(json.dumps(return_data), mimetype='application/json')


@app.route('/next', methods=['GET'])
def get_next():
    """Get Next Page of Query Results.

        Returns next page of query results ordered by most recent order and filter to client for display. Also sends
        next/prev booleans for navigation buttons.

        Returns:
            JSON Response containing next page of query results, navigation button bools.
    """
    json_array = []
    entries[0], cursorObject[0], more[0] = orderedQuery[0].fetch_page(50, start_cursor=cursorObject[0])
    return_data = {"records": json_array, "next": more[0], "prev": True}
    for i in entries[0]:
        json_array.append(i.json_data)
    return Response(json.dumps(return_data), mimetype='application/json')


@app.route('/prev', methods=['GET'])
def get_prev():
    """Get Prev Page of Query Results.

        Returns prev page of query results ordered by most recent order and filter to client for display. Also sends
        next/prev booleans for navigation buttons.

        TODO: simplify to reduce extra page fetch.

        Returns:
            JSON Response containing prev page of query results, navigation button bools.
    """
    json_array = []
    entries[0], cursorObject[0], r_more[0] = revOrderedQuery[0].fetch_page(100,
                                                                           start_cursor=cursorObject[0],
                                                                           keys_only=True)
    entries[0], cursorObject[0], more[0] = orderedQuery[0].fetch_page(50,
                                                                      start_cursor=cursorObject[0])
    return_data = {"records": json_array, "next": more[0], "prev": r_more[0]}
    for i in entries[0]:
        json_array.append(i.json_data)
    return Response(json.dumps(return_data), mimetype='application/json')


@app.route('/save', methods=['POST'])
def save_data():
    """Order Datastore.

        Receives JSON containing edited client-side entries to save to datastore. Currently called on every individual
        "save" and "delete" action to prevent loss of changes if the client ends session earlier than expected.
        Therefore, should only receive one edited entry at a time despite ability to handle collections.

        Returns:
            JSON success message.
    """
    edited_data = request.get_json()
    if len(edited_data['records']) > 0:
        for i in edited_data['records']:
            record = JsonData(json_data=i, yearValue=str(i['Year']), causeValue=i['CauseName'], regionValue=i['State'])
            if i['editType'] == 'delete':
                delete_query = JsonData.query(JsonData.id == str(i['Year'])
                                              + i['CauseName']
                                              + i['State'])
                delete_query.get().key.delete()
            else:
                edit_query = JsonData.query(JsonData.id == str(i['Year'])
                                            + i['CauseName']
                                            + i['State'])
                if edit_query.get() is not None:
                    record = edit_query.get()
                    record.json_data = i
                record.put()
    return jsonify(status="success", data=data)


@app.route('/duplicates')
def delete_duplicates():
    q = JsonData.query().order(JsonData.id)
    h = q.fetch_page(1)
    print(h)
    for i in q.fetch():
        if i is not h and i.id is h.id:
            if i.date > h.date:
                i.key.delete()
            else:
                h.key.delete()
        h = i
    return render_template('index.html')


if __name__ == '__main__':
    app.run()
