from kafka import KafkaProducer, KafkaConsumer
import json


class MessageProducer:
    def __init__(self, broker, topic):
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=self.broker,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            acks=0,
            api_version=(2, 5, 0),
            retries=3,
        )

    def send_message(self, msg, auto_close=True):
        try:
            future = self.producer.send(self.topic, msg)
            self.producer.flush()  # 비우는 작업
            if auto_close:
                self.producer.close()
            future.get(timeout=2)
            return {"status_code": 200, "error": None}
        except Exception as exc:
            raise exc


class MessageConsumer:
    def __init__(self, broker, topic):
        self.broker = broker
        self.consumer = KafkaConsumer(
            topic,  # Topic to consume
            bootstrap_servers=self.broker,
            value_deserializer=lambda x: x.decode(
                "utf-8"
            ),  # Decode message value as utf-8
            group_id="my-group",  # Consumer group ID
            auto_offset_reset="earliest",  # Start consuming from earliest available message
            enable_auto_commit=True,  # Commit offsets automatically
        )

    def receive_message(self):
        try:
            for message in self.consumer:
                print(message)
        except Exception as exc:
            raise exc


"""
# 브로커와 토픽명을 지정한다.
broker = ["localhost:9092", "localhost:9093", "localhost:9094"]
topic = "my-topic"
pd = MessageProducer(broker, topic)

msg = {"name": "John", "age": 30}
res = pd.send_message(msg)
print(res)

# 브로커와 토픽명을 지정한다.
broker = ["localhost:9092", "localhost:9093", "localhost:9094"]
topic = "my-topic"
cs = MessageConsumer(broker, topic)
cs.receive_message()
"""