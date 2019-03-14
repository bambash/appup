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

## usage
control uptime via HTTP
```bash
$ kubectl apply -f https://raw.githubusercontent.com/bambash/appup/master/examples/with-http-check.yml
deployment.extensions/nginx created

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
nginx-5cf45645dc-nbh4h   2/2     Running   0          33s
$ kubectl port-forward nginx-5cf45645dc-nbh4h 9999:9999

$ curl localhost:9999/down
app is down

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
nginx-5cf45645dc-nbh4h   1/2     Running   0          2m20s

$ curl localhost:9999/up
app is up

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
nginx-5cf45645dc-nbh4h   2/2     Running   0          2m30s
```
control uptime via shell exec
```bash
$ kubectl exec -ti nginx-5cf45645dc-nbh4h -c appup -- sh -c 'rm /pod/up.txt'

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
nginx-5cf45645dc-nbh4h   1/2     Running   0          3m34s

$ kubectl exec -ti nginx-5cf45645dc-nbh4h -c appup -- sh -c 'touch /pod/up.txt'

$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
nginx-5cf45645dc-nbh4h   2/2     Running   0          4m23s
```

Other pods running within the cluster as Jobs or CronJobs could also control uptime by sending a request to the appup container.

## deployment example
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
              command: ['/bin/sh', '-c', 'touch /pod/up.txt']
          ## remove the up.txt when kill signal received
          preStop:
            exec:
              command: ['/bin/sh', '-c', 'rm -f /pod/up.txt']
        ## mount pod volume
        volumeMounts:
        - name: pod
          mountPath: /pod
        ports:
        - containerPort: 9999
      - name: container-without-health
        image: app-without-health
        imagePullPolicy: Always
        ## probe via shell
        readinessProbe:
          exec:
            command:
            - cat
            - /pod/up.txt
          periodSeconds: 1
          successThreshold: 1
          timeoutSeconds: 1
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
              command: ['/bin/sh', '-c', 'touch /pod/up.txt']
          ## remove the up.txt when kill signal received
          preStop:
            exec:
              command: ['/bin/sh', '-c', 'rm -f /pod/up.txt']
        volumeMounts:
        - name: pod
          mountPath: /pod
        ports:
        - containerPort: 9999
      - name: nginx
        image: nginx
        imagePullPolicy: Always
        ## probe via http
        readinessProbe:
          failureThreshold: 1
          httpGet:
           path: /health
           port: 9999
           scheme: HTTP
          periodSeconds: 1
          successThreshold: 1
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
In a perfect world all applications have health checking and this would not be needed. However, I've experienced some pains when trying to control uptime on applications that have been migrated into Kubernetes that do not have a simple way to do health checks. The code owners for these apps usually don't have the time, experience, or business support to implement native health checks.
