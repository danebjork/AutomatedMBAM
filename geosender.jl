#!/usr/bin/env julia

module GeoSender

    using ZMQ
    using JSON

    function send_to_py(data)
        context = Context()
        data_sender = Socket(context, PUSH)
        ZMQ.connect(data_sender, "tcp://127.0.0.1:5556")

        to_send = JSON.json(data)
        ZMQ.send(data_sender, to_send)
        ZMQ.close(data_sender)
        ZMQ.close(context)
    end
end

