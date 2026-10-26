use std::fmt;

#[derive(Debug)]
pub(crate) enum Error {
    Blocked(String),
    Io(std::io::Error),
    Json(serde_json::Error),
    Interrupted,
}

impl Error {
    pub(crate) fn blocked(message: impl Into<String>) -> Self {
        Self::Blocked(message.into())
    }

    pub(crate) fn public_message(&self) -> &str {
        match self {
            Self::Blocked(message) => message,
            Self::Io(_) => "Local I/O failed; inspect the private run record.",
            Self::Json(_) => "Invalid structured data; inspect the private run record.",
            Self::Interrupted => "The worker was interrupted.",
        }
    }
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(error) => write!(f, "Local I/O: {error}"),
            Self::Json(error) => write!(f, "Structured data: {error}"),
            _ => f.write_str(self.public_message()),
        }
    }
}

impl std::error::Error for Error {}

impl From<std::io::Error> for Error {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}
impl From<serde_json::Error> for Error {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}

pub(crate) type Result<T> = std::result::Result<T, Error>;
