pub struct Resolution {
    pub target: Option<u64>,
    pub confidence: u8,
}

pub fn unresolved() -> Resolution {
    Resolution { target: None, confidence: 0 }
}

pub fn consume(result: Resolution) -> bool {
    let Resolution { target, confidence } = result;
    target.is_some() && confidence > 0
}
