-- Insert test data
INSERT INTO authors (name, bio, email)
SELECT 
    'Author ' || i,
    'Bio for author ' || i,
    'author' || i || '@example.com'
FROM generate_series(1, 1000) i;

INSERT INTO articles (title, subtitle, content, author_id, status, published_at)
SELECT 
    'Article Title ' || i,
    'Subtitle for article ' || i,
    'Content for article ' || i || ' ' || repeat('Lorem ipsum dolor sit amet. ', 100),
    (i % 1000) + 1,
    'published',
    timestamp '2020-01-01' + (random() * (now() - timestamp '2020-01-01'))
FROM generate_series(1, 1000000) i;