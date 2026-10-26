use crate::error::{Error, Result};
use serde::Serialize;
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};
use std::path::Path;

pub(crate) fn write_private(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .mode(0o600)
        .open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}
pub(crate) fn atomic_json(path: &Path, value: &impl Serialize) -> Result<()> {
    let temporary = path.with_extension("tmp");
    let mut bytes = serde_json::to_vec_pretty(value)?;
    bytes.push(b'\n');
    write_private(&temporary, &bytes)?;
    fs::rename(temporary, path)?;
    Ok(())
}
pub(crate) struct Lock {
    file: File,
}

impl Drop for Lock {
    fn drop(&mut self) {
        // Release explicitly: a concurrently spawned child can briefly inherit
        // the open file description before exec closes its descriptor.
        let _ = self.file.unlock();
    }
}

pub(crate) fn lock(directory: &Path) -> Result<Lock> {
    fs::create_dir_all(directory)?;
    fs::set_permissions(directory, fs::Permissions::from_mode(0o700))?;
    let file = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .mode(0o600)
        .open(directory.join("worker.lock"))?;
    file.try_lock()
        .map_err(|_| Error::blocked("Worker lock unavailable; another worker may be running."))?;
    Ok(Lock { file })
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn local_lock_excludes_a_second_worker() {
        let dir = tempfile::tempdir().expect("temp");
        let first = lock(dir.path()).expect("first");
        assert!(lock(dir.path()).is_err());
        drop(first);
        assert!(lock(dir.path()).is_ok());
    }

    #[test]
    fn receipts_and_run_directories_are_private() {
        let dir = tempfile::tempdir().expect("temp");
        let _lock = lock(dir.path()).expect("lock");
        let path = dir.path().join("receipt.json");
        atomic_json(&path, &serde_json::json!({"stage":"claimed"})).expect("receipt");
        assert_eq!(
            fs::metadata(dir.path())
                .expect("directory")
                .permissions()
                .mode()
                & 0o777,
            0o700
        );
        assert_eq!(
            fs::metadata(path).expect("receipt").permissions().mode() & 0o777,
            0o600
        );
    }
}
