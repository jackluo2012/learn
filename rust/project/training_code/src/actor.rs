use anyhow::{Ok, Result};
use tokio::sync::{mpsc, oneshot};

pub struct Actor<State, Request, Reply> {
    // 接收端的 mpsc
    receiver: mpsc::Receiver<ActorMessage<Request, Reply>>,
    state: State,
}

impl<State, Request, Reply> Actor<State, Request, Reply>
where
    State: Default + Send + 'static,
    Request: HandCall<State, Request, Reply, State = State, Reply = Reply> + Send + 'static,
    Reply: Send + 'static,
{
    pub fn spawn(mailbox: usize) -> Pid<Request, Reply> {
        let (sender, receiver) = mpsc::channel(mailbox);
        let mut actor: Actor<State, Request, Reply> = Actor {
            receiver,
            state: State::default(),
        };
        tokio::spawn(async move {
            while let Some(msg) = actor.receiver.recv().await {
                let reply = msg.data.handle_call(&mut actor.state).unwrap();
                msg.sender.send(reply);
            }
        });
        Pid { sender }

        // todo!()
    }
}

pub struct ActorMessage<Request, Reply> {
    pub data: Request,
    pub sender: oneshot::Sender<Reply>,
}

pub trait HandCall<State, Request, Reply>: Sized {
    type State;
    type Reply;

    fn handle_call(&self, state: &mut Self::State) -> Result<Self::Reply>;
}
#[derive(Clone)]
pub struct Pid<Request, Reply> {
    sender: mpsc::Sender<ActorMessage<Request, Reply>>,
}

impl<Request, Reply> Pid<Request, Reply> {
    pub fn new(sender: mpsc::Sender<ActorMessage<Request, Reply>>) -> Self {
        Self { sender }
    }

    pub async fn send(&self, data: Request) -> Result<Reply> {
        let (sender, receiver) = oneshot::channel();
        let msg = ActorMessage { sender, data };
        let _ = self.sender.send(msg);
        Ok(receiver.await?)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    impl HandCall<usize, usize, usize> for usize {
        type State = usize;
        type Reply = usize;

        fn handle_call(&self, state: &mut Self::State) -> Result<Self::Reply> {
            *state += 1;
            Ok(self + 1)
        }
    }

    #[tokio::test]
    async fn it_works() {
        assert_eq!(2 + 2, 4);
        let pid: Pid<usize, usize> = Actor::spawn(20);
        let result = pid.send(42).await.unwrap();
        assert_eq!(result, 43);
    }
}
