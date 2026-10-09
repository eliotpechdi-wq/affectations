-- Base des choix de l'application Affectations SSA (à exécuter une fois dans le projet Supabase).
-- Profils sans mot de passe : la clé publique « anon » peut lire et écrire ces deux tables.

create table if not exists public.profils (
  nom      text primary key check (char_length(nom) between 1 and 30),
  cree_le  timestamptz not null default now()
);

create table if not exists public.choix (
  profil   text not null references public.profils(nom) on delete cascade,
  site_id  text not null,
  statut   text not null default '' check (statut in ('', 'retenue', 'ecartee')),
  note     text not null default '' check (char_length(note) <= 4000),
  maj      timestamptz not null default now(),
  primary key (profil, site_id)
);

alter table public.profils enable row level security;
alter table public.choix   enable row level security;

drop policy if exists "profils accessibles" on public.profils;
create policy "profils accessibles" on public.profils for all to anon using (true) with check (true);

drop policy if exists "choix accessibles" on public.choix;
create policy "choix accessibles" on public.choix for all to anon using (true) with check (true);
