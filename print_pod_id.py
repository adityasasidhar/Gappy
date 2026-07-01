from lemma_sdk import Pod
pod = Pod.from_env()
print("POD ID:", pod.pod_id)
# let's print all attributes of pod
print("POD attributes:", dir(pod))
