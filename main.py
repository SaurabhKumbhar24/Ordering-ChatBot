from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_order = {}

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_context = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_context[0]['name'])

    intent_handler_dict = {
        "order.add": order_add,
        "order.remove": order_remove,
        "order.complete": order_complete
    }
     
    return intent_handler_dict[intent](parameters,session_id)

def order_add(parameters: dict, session_id: str):

    food_items = parameters['food-item']
    quantities = parameters['number']

    if len(food_items) != len(quantities):
        fulfillmentTxt = "Sorry I did'nt understand can you please specify food items and its quantities?"
    else:
        new_food_dict = dict(zip(food_items, quantities))
        if session_id in inprogress_order:
            (inprogress_order[session_id]).update(new_food_dict)
        else:
            inprogress_order[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_order[session_id])
        
        fulfillmentTxt = f"So far you have: {order_str}. Would you like to have anything else?"

    return JSONResponse(content={"fulfillmentText":fulfillmentTxt})

def order_remove(parameters, session_id: str):
    
    if session_id not in inprogress_order:
        fulfillmentTxt = "I'm having trouble finding your order. Sorry Can you please place new order ?"
    else:
        current_order = inprogress_order[session_id]
        food_items = parameters['food-item']

        removed_items = []
        no_such_items = []

        for item in food_items:
        
            if item not in current_order:
                no_such_items.append(item)

                pass
            else:
                removed_items.append(item)
                del current_order[item]

        if len(removed_items) > 0:
            fulfillmentTxt = f'Removed {", ".join(removed_items)} from your order!'
        
        if len(no_such_items) > 0:
            fulfillmentTxt = f'Your current order does not have {" ,".join(no_such_items)}'
        
        if len(current_order.keys()) == 0:
            fulfillmentTxt += "Your order is empty."
        else:
            order_str = generic_helper.get_str_from_food_dict(current_order)
            fulfillmentTxt += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={ "fulfillmentText": fulfillmentTxt })


def order_complete(parameters, session_id: str):
    if session_id in inprogress_order:
        order = inprogress_order[session_id]
        order_id = save_to_db(order)
        if order_id != -1:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillmentText = f"Awesome your order is placed. Your order id #{order_id} and your order total is {order_total}."
        else:
            fulfillmentText = "Hey I'm having trouble placing an order."
    else: 
        fulfillmentText = "I'm having trouble finding your order. Sorry Can you please place new order ?"
    
    del inprogress_order[session_id]
    
    return JSONResponse(content={
        "fulfillmentText":fulfillmentText
    })

def save_to_db(order : dict):
    
    next_order_id = db_helper.get_next_order_id()

    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(food_item, quantity, next_order_id)

        if rcode == -1:
            return -1
    
    return next_order_id