use std::sync::{Arc, RwLock};

use axum::{
    middleware::AddExtension,
    extract::{FromRequest, Request}, http::{self,Response, StatusCode}, middleware::AddExtension, response::{self,Html, IntoResponse}, routing::{get, post, Route}, Json, Router
};
use serde::{Deserialize, Serialize};
use jsonwebtoken::{encode, decode, Header, Algorithm, Validation, EncodingKey, DecodingKey};




const SECRET: &[u8] = b"secret";


/// Our claims struct, it needs to derive `Serialize` and/or `Deserialize`
#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    id: usize,
    name: String,
    exp: usize,
}
#[derive(Debug, Serialize, Deserialize)]
struct Todo {
    pub id: usize,
    pub title: String,
    pub completed: bool,
}
#[derive(Debug, Deserialize)]
struct LoginRequest { 
    pub username: String,
    pub password: String,
}

#[derive(Debug, Serialize)]
struct LoginResponse { 
    pub token: String,
}

#[derive(Debug, Deserialize)]
struct CreateTodo {
    pub title: String,
}
#[derive(Debug,Default)]
struct TodoStore { 
    items: Arc<RwLock<Vec<Todo>>>,
}

#[tokio::main]
async fn main() { 
    // initialize tracing
    // tracing_subscriber::fmt::init();
    let store = TodoStore::default();
    // build our application with a route
    let app = Router::new()
        // `GET /` goes to `root`
        .route("/", get(index_handler))
        // `POST /users` goes to `create_user`
        .route("/todos", get(todos_handler).post(create_todo_handler).layer(AddExtension::<TodoStore>))
        .route("/login",post(login_handler));
    // run our app with hyper, listening globally on port 3000
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn index_handler() -> Html<&'static str> {
    Html("Hello, World!")
}

async fn todos_handler() -> Json<Vec<Todo>> {
    Json(vec![
        Todo {
            id: 1,
            title: "Todo 1".to_string(),
            completed: false,
        },
        Todo {
            id: 2,
            title: "Todo 2".to_string(),
            completed: true,
        },
    ])
}

async fn create_todo_handler(claims: Claims,Json(_todo): Json<CreateTodo>) -> (StatusCode) {
    (StatusCode::CREATED)
}

async fn login_handler(Json(login): Json<LoginRequest>) -> (StatusCode, Json<LoginResponse>) {
    // let header = Header::new(Algorithm::HS512);
    // let key = EncodingKey::from_secret("secret".as_ref());
    // let token = encode(&header, &payload, &key).unwrap();
    // (StatusCode::OK, Json(payload))
    let claims = Claims { 
        id: 1,
        name: "John Doe".to_string(),
        exp: 0,
    };
    let token = encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(SECRET),
    ).unwrap();
    (StatusCode::OK, Json(LoginResponse { token }))
}

impl<B> FromRequest<B> for Claims
where
    B: Send + Sync,
{
    type Rejection = HttpError;

    async fn from_request(req: Request, state: &B) -> Result<Self, Self::Rejection> {
        
        let token = req.headers().get("Authorization").and_then(|h| h.to_str().ok()).unwrap();
        
        let token = decode::<Claims>(&token, &DecodingKey::from_secret(SECRET), &Validation::default()).unwrap();
        Ok(token.claims)
    }
}

#[derive(Debug)]
enum HttpError {
    Auth,
    Internal,
    
}

impl IntoResponse for HttpError {
    fn into_response(self) -> response::Response {
        let (code,msg) = match self {
            HttpError::Auth => (StatusCode::UNAUTHORIZED, "Unauthorized"),
            HttpError::Internal => (StatusCode::INTERNAL_SERVER_ERROR, "Internal Server Error"),
        };
        (code,msg).into_response()
    }
}

fn get_next_id(store: &TodoStore) -> usize { 
    let items = store.items.read().unwrap();
    if items.is_empty() {
        1
    } else {
        items.last().unwrap().id + 1
    }
}