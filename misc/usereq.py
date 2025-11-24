import requests

x = requests.get('https://www.google.com')

print(x.text)
print(x.status_code)
print(x.json)
print(type(x.json))
print(x.headers)

if x.status_code == 200:
    print("Success!")
elif x.status_code == 404:
    print("Not Found.")