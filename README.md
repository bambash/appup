# appup
This simple webapp was designed to run as a sidecar container inside of Kubernetes pods. It is intended to serve as a traffic controller switch for applications that do not have native health checks. __Do not use this as a replacement for applications with proper health/liveness built in.__

The goal was to create a small python webserver using the native libraries that listens on 3 endpoints:
```
/up
/down
/health
```

- calling `/up` will 'touch' a temporary `UP_FILE`, defaults to `/pod/up.txt`, and return a `200` status code
- calling `/down` will remove the `UP_FILE`, and return a `200`. If the `UP_FILE` doesn't exist, it will return a `503`.
- calling `/health` will check for the existince of `UP_FILE`, and return a `200` if present. Otherwise return `503`.
- configurable using two environment variables, `UP_FILE` (default `/pod/up.txt`) and `UP_PORT` (default `9999`)

## example
Kubernetes probe using shell
```YAML
...
      containers:
      - name: appup
        image: bambash/appup:latest
        imagePullPolicy: Always
        lifecycle:
          ## create the up.txt when pod is created
          postStart:
            exec:
              command: ['touch']
              args: ['/pod/up.txt']
        ## mount pod volume
        volumeMounts:
        - name: pod
          mountPath: /pod
        ports:
        - containerPort: 9999
      - name: container-without-health
        image: app-without-health
        imagePullPolicy: Always
        lifecycle:
          ## remove the up.txt when kill signal received
          preStop:
            exec:
              command: ['rm']
              args: ['-f', '/pod/up.txt']
        ## probe via shell
        readinessProbe:
          exec:
            command:
            - cat
            - /pod/up.txt
            initialDelaySeconds: 10
            successThreshold: 3
            periodSeconds: 1
            failureThreshold: 1
        ## mount pod volume
        volumeMounts:
        - name: pod
          mountPath: /pod
      ## create a pod volume that is shared with all containers
      volumes:
      - name: pod
        emptyDir: {}
...
```

Kubernetes probe using HTTP
```YAML
...
      containers:
      - name: appup
        image: bambash/appup:latest
        imagePullPolicy: Always
        lifecycle:
          ## create the up.txt when pod is created
          postStart:
            exec:
              command: ['touch']
              args: ['/pod/up.txt']
        volumeMounts:
        - name: pod
          mountPath: /pod
        ports:
        - containerPort: 9999
      - name: container-without-health
        image: app-without-health
        imagePullPolicy: Always
        lifecycle:
          ## remove the up.txt when kill signal received
          preStop:
            exec:
              command: ['rm']
              args: ['-f', '/pod/up.txt']
        ## probe via http
        readinessProbe:
          failureThreshold: 1
          httpGet:
           path: /health
           port: 9999
           scheme: HTTP
          periodSeconds: 10
          successThreshold: 3
          timeoutSeconds: 1
        volumeMounts:
        - name: pod
          mountPath: /pod
      volumes:
      - name: pod
        emptyDir: {}
```
## gotchas
`UP_FILE` needs to be created manually. This can be done by calling `/up` or touching the `UP_FILE` at somepoint during the pod lifecycle. 

Operators will need to fully understand the implicatons of controlling  upime manually.

## why?
In a perfect world all applications have health checking and this would not be needed. However, I've experienced some pains when trying to control uptime on applications that have been migrated into Kubernetes that do not have health checks. The code owners for these apps usually don't have the time, experience, or business support to implement native health checks.

While you could use Kubernetes port checking or increase the sleep durations, I feel that this gives the operators a little more flexibility.