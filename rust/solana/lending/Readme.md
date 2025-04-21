####
```
let source_path = proc_macro2::Span::call_site().source_file().path();
    |                                                                  ^^^^^^^^^^^ method not found in `Span`
```
```shell
anchor build --no-idl
``