# GoogLeNet-API
RESTful API for objection detection using GoogLeNet

###Start the server
```
docker run -p 3000:3001 mbartoli/googlenet-api
```


###Example usage 
```
http:/localhost:3000/detection -d "data=http://xemanhdep.com/gallery/cute_cat1/cute_cat102.jpg" -X PUT
```
```
[
    61.8, 
    "tabby, tabby cat", 
    281
]

```
