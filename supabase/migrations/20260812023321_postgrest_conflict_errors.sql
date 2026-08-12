begin;

do $$
declare
  function_signature regprocedure;
  function_definition text;
  updated_definition text;
begin
  function_signature := to_regprocedure(
    'public.epicenter_transition_ticket(text,integer,text,text,boolean,text,text)'
  );
  if function_signature is null then
    raise exception 'epicenter_transition_ticket is not installed';
  end if;
  function_definition := pg_get_functiondef(function_signature);
  if position('''PT409''' in function_definition) = 0 then
    updated_definition := replace(function_definition, '''40001''', '''PT409''');
    if updated_definition = function_definition then
      raise exception 'ticket transition stale-version error was not found';
    end if;
    execute updated_definition;
  end if;

  function_signature := to_regprocedure(
    'public.epicenter_decide_allocation(text,integer,text,text,text,text)'
  );
  if function_signature is null then
    raise exception 'epicenter_decide_allocation is not installed';
  end if;
  function_definition := pg_get_functiondef(function_signature);
  if position('''PT409''' in function_definition) = 0 then
    updated_definition := replace(function_definition, '''40001''', '''PT409''');
    if updated_definition = function_definition then
      raise exception 'allocation decision stale-version error was not found';
    end if;
    execute updated_definition;
  end if;
end;
$$;

commit;
