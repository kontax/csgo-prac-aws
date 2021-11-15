var $table = $('#table');
    var mydata = 
[{
    "taskArn": "arn:aws:ecs:eu-west-1:150673653788:task/csgo-prac-aws-cluster/78234ff764fb48e0b4ef3044ee60e435",
    "startedAt": "2021-11-15 20:48:24",
    "lastStatus": "RUNNING",
    "desiredStatus": "RUNNING",
    "cpu": "2048",
    "memory": "8192",
    "overrides": {
        "containerOverrides": [{
            "name": "csgo-prac-aws-container",
            "environment": [{
                "name": "TICKRATE", 
                "value": "64"
            }, {
                "name": "MAP", 
                "value": "de_dust2"
            }, {
                "name": "MAPGROUP", 
                "value": "mg_active"
            }]
        }],
        "inferenceAcceleratorOverrides": []
    }, 
    "stopCode": null,
    "stoppedReason": null,
    "stoppingAt": null,
    "stoppedAt": null
}]

$(function () {
    $('#table').bootstrapTable({
        data: mydata
    });
});
